import inspect
import os
from dolfin import Mesh

class MeshFactory(object):
    
  @staticmethod
  def get_study_region(km):
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))
    mesh     = home + '/antarctica/study_region_{0}.xml'.format(km)
    return Mesh(mesh)

  @staticmethod
  def get_study_region_test():
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))                     
    mesh     = home + '/antarctica/study_region_test.xml'
    return Mesh(mesh)     


  @staticmethod
  def get_greenland_detailed():
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))
    mesh     = home + '/greenland/greenland_detailed_mesh.xml' 
    return Mesh(mesh)
 
  @staticmethod
  def get_greenland_medium():
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))
    mesh     = home + '/greenland/greenland_medium_mesh.xml' 
    return Mesh(mesh)


  @staticmethod
  def get_greenland_coarse():
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))
    mesh     = home + '/greenland/greenland_coarse_mesh.xml' 
    return Mesh(mesh)


  @staticmethod
  def get_antarctica():
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))
    mesh     = home + '/antarctica/antarctica_50H_5l.xml' 
    return Mesh(mesh)


  @staticmethod
  def get_circle():
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    home     = os.path.dirname(os.path.abspath(filename))
    mesh     = home + '/test/circle.xml' 
    return Mesh(mesh)



