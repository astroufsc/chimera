import os
import shutil


def isstr(x):
  """Return True if x is a string"""
  try:
    return str(x)==x
  except Exception:
    return False

def getInType(x):
  """Check to see if the input is a valid image list or a valid directory"""
  while(1):
    if isinstance(x,list):
      if len(x)!=0:
        return 'ImageList'
   
     
    elif isinstance(x,str):
      if os.path.exists(x)==True:
        return 'Directory'
      
      else:
        print 'Not a valid Directory'
        break
    else:
      print 'Not a valid input type'
      break
      
