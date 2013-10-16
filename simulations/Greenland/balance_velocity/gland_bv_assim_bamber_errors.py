import sys
import os
src_directory = '../../../'
sys.path.append(src_directory)

from src.utilities     import DataInput,DataOutput
from data.data_factory import DataFactory
from src.physics       import VelocityBalance_2
from pylab             import *
from dolfin            import *
import os

set_log_active(True)

# collect the raw data :
searise = DataFactory.get_searise()
measure = DataFactory.get_gre_measures()
bamber  = DataFactory.get_bamber()

direc = os.path.dirname(os.path.realpath(__file__))

# load a mesh :
mesh    = Mesh("./mesh.xml")

# create data objects to use with varglas :
dsr     = DataInput(None, searise, mesh=mesh, create_proj=True)
dbam     = DataInput(None, bamber,      mesh=mesh)
dms     = DataInput(None, measure, mesh=mesh, create_proj=True, flip=True)

dms.change_projection(dsr)

dbam.set_data_min('H', 200.0, 200.0)
dbam.set_data_min('h', 1.0, 1.0)
dms.set_data_min('sp',0.0,-2e9)

# Make velocity error data easier to handle:
MAX_V_ERR = 500
NO_DATA = -99
dms.set_data_min('ex',-MAX_V_ERR,NO_DATA)
dms.set_data_max('ex',MAX_V_ERR,NO_DATA)
dms.set_data_min('ey',-MAX_V_ERR,NO_DATA)
dms.set_data_max('ey',MAX_V_ERR,NO_DATA)
print 'H'
H     = dbam.get_projection("H")
print 'H0'
H0    = dbam.get_projection("H")
print 'S'
S     = dbam.get_projection("h")
print 'Herr'
Herr  = dbam.get_projection("Herr")

print 'adot'
adot  = dsr.get_projection("adot")

print 'Uobs'
Uobs   = dms.get_projection("sp")
print 'vxerr'
vxerr  = dms.get_projection("ex",near=True) # no interpolation
print 'vyerr'
vyerr  = dms.get_projection("ey",near=True)

print 'verr'
verr = project(sqrt(vxerr*2+vyerr**2 + 1e-3))

Uobs.vector()[Uobs.vector().array()<0] = 0.0

U_sar_spline = dms.get_spline_expression("sp")
ex_spline    = dms.get_spline_expression("ex") # not sure why

# Desire a mask that only uses lower error velocities and plug flow velocities
SLIDE_THRESHOLD = 50.   # to be replaced with calculation
V_ERROR_THRESHOLD = .05 # errors larger than this fraction ignored

insar_mask = CellFunctionSizet(mesh)
insar_mask.set_all(0)
for c in cells(mesh):
    x,y = c.midpoint().x(),c.midpoint().y()
    Uval = U_sar_spline(x,y)
    exval = ex_spline(x,y)
    verrval = verr(x,y)

    if Uval>SLIDE_THRESHOLD and exval != NO_DATA\
                            and verrval/Uval < V_ERROR_THRESHOLD:
        insar_mask[c] = 1
        

# Create a per vertex data type that has velocity errors where mask is true
# and infinity else where
# Seems like a lot of thrashing around, should come up with a cleaner approach
Uerr = VertexFunctionDouble(mesh)
Uerr.set_all(500)  # This is 'infinite' error, the search is unbound
for v in vertices(mesh):
    x,y = v.x(0), v.x(1)
    Uval = U_sar_spline(x,y)
    exval = ex_spline(x,y)
    verrval = verr(x,y)

    if Uval>SLIDE_THRESHOLD and exval != NO_DATA\
                            and verrval/Uval < V_ERROR_THRESHOLD:
        Uerr[v] = verrval


#Write back to field to check output as written file
verr.vector().array()[:] = Uerr.array()

# Problem definition
prb   = VelocityBalance_2(mesh, H, S, adot, 8.0,Uobs=Uobs,Uobs_mask=insar_mask)

n = len(mesh.coordinates())

# IO
Uopt_file = File('results/Uopt.pvd')
Uopt_file_xml = File('results/Uopt.xml')
Uobs_file = File('results/Uobs.pvd')
Uerr_file = File('results/Uerr.pvd')
H_file = File('results/H.pvd')
adot_file = File('results/adot.pvd')
dHdt_file = File('results/dHdt.pvd')
delta_H_file = File('results/deltaH.pvd')
delta_U_file = File('results/deltaU.pvd')
Herr_file = File('results/Herr.pvd')
ex_file = File('results/ex.pvd')
ey_file = File('results/ey.pvd')

def _I_fun(x):
    prb.Uobs.vector()[:] = x[:n]
    prb.adot.vector()[:] = x[n:2*n]
    prb.H.vector()[:]    = x[2*n:]
    prb.solve_forward()
    I = assemble(prb.I)
    return I

def _J_fun(x):
    prb.Uobs.vector()[:] = x[:n]
    prb.adot.vector()[:] = x[n:2*n]
    prb.H.vector()[:]    = x[2*n:]
    # I/O
    Uopt_file << prb.Ubmag
    delta_U_file<<project(Uobs - prb.Ubmag)
    Uobs_file << prb.Uobs
    H_file << prb.H
    adot_file << prb.adot
    delta_H_file << project(prb.H - H0,dbam.func_space)
    dHdt_file << project(prb.residual-prb.adot,dbam.func_space)
    Uopt_file_xml << prb.Ubmag

    # Checking the error files:
    Uerr_file << verr
    Herr_file << Herr
    ex_file << vxerr
    ey_file << vyerr

    prb.solve_adjoint()
    g = prb.get_gradient()

    return hstack(g)

from scipy.optimize import fmin_l_bfgs_b

x0 = hstack((Uobs.vector().array(),adot.vector().array(),H.vector().array()))

amerr = 0.15
aaerr = 0.25
ahat_bounds = [(min(r-amerr*abs(r),r-aaerr),max(r+amerr*abs(r),r+aaerr)) for r in adot.vector().array()] 

small_u = 1. # Minimal error in velocity
Uobs_bounds = [(min(Uobs_i - Uerr_i,Uobs_i-small_u), max(Uobs_i+Uerr_i,Uobs_i+small_u)) for Uobs_i,Uerr_i in zip(Uobs.vector().array(),Uerr.array())] 

small_h = 0.1 # Minimal uncertainty: replaces Bamber's zeros.
H_bounds = [(min(H_i - Herr_i,H_i-small_h), max(H_i + Herr_i,H_i+small_h)) \
            for H_i,Herr_i in zip(H.vector().array(),Herr.vector().array())] 

bounds = Uobs_bounds+ahat_bounds+H_bounds

#fmin_l_bfgs_b(_I_fun,x0,fprime=_J_fun,bounds=bounds,iprint=1)