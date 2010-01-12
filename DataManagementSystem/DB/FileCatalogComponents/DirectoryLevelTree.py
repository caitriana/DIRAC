########################################################################
# $HeadURL:  $
########################################################################

""" DIRAC FileCatalog component representing a directory tree with 
    enumerated paths
"""

__RCSID__ = "$Id:  $"

import time, os
from types import *
from DIRAC import S_OK, S_ERROR

MAX_LEVELS = 10

class DirectoryLevelTree:
  """ Class managing Directory Tree as a simple self-linked structure with full
      directory path stored in each node
  """
  def __init__(self, database=None):
    """ Constructor
    """
    self.db = database
    
  def setDatabase(self,database):
    
    self.db = database  
    
  def findDir(self,path):
    
    req = "SELECT DirID,Level from FC_DirectoryLevelTree WHERE DirName='%s'" % path
    result = self.db._query(req)
    if not result['OK']:
      return result
    
    if not result['Value']:
      return S_OK('')
    
    res = S_OK(result['Value'][0][0])  
    res['Level'] = result['Value'][0][1]
    return res
  
  def removeDir(self,path):
    """ Remove directory
    """

    result = self.findDir(path)
    if not result['OK']:
      return result   
    if not result['Value']:
      return S_OK()
    
    dirID = result['Value']
    req = "DELETE FROM FC_DirectoryLevelTree WHERE DirID=%d" % dirID
    result = self.db._update(req)
    return result

  def __getNumericPath(self,dirID):
    """ Get the enumerated path of the given directory
    """
    
    epaths = []
    for i in range(1,11,1):
      epaths.append("LPATH%d" % i)
    epathString = ','.join(epaths)  
    
    req = 'SELECT LEVEL,%s FROM FC_DirectoryLevelTree WHERE DirID=%d' % (epathString,dirID)
    result = self.db._query(req)
    if not result['OK']:
      return result   
    if not result['Value']:
      return S_OK([])
    
    row = result['Value'][0]
    level = row[0]
    epathList = []
    for i in range(level):
      epathList.append(row[i+1])
      
    return S_OK(epathList)  
    

  def makeDir(self,path):
        
    result = self.findDir(path)
    if not result['OK']:
      return result
    dirID = result['Value']
    if dirID:
      return S_OK(dirID)  
       
    dpath = path 
    if path == '/':
      dirName = '/'
      level = 0
      elements = []
      parentDirID = 0
    else:  
      if path[0] == "/":
        dpath = path[1:]  
      elements = dpath.split('/')
      level = len(elements)
      dirName = elements[-1]
      result = self.getParent(path)
      if not result['OK']:
        return result
      parentDirID = result['Value']
    
    epathList = []
    if parentDirID:
      result = self.__getNumericPath(parentDirID)
      if not result['OK']:
        return result
      epathList = result['Value']
    
    names = ['DirName','Level','Parent']
    values = [path,level,parentDirID]
    if path != '/':
      for i in range(1,level,1):                
        names.append('LPATH%d' % i) 
        values.append(epathList[i-1])
      
    result = self.db._insert('FC_DirectoryLevelTree',names,values)    
    if not result['OK']:
      return result
    dirID = result['lastRowId']
    
    # Update the path number
    if parentDirID:
      lPath = "LPATH%d" % (level)
      result = self.db._getConnection()
      conn = result['Value']
      req = "LOCK TABLES FC_DirectoryLevelTree WRITE; "
      result = self.db._query(req,conn)
      req = " SELECT @tmpvar:=max(%s)+1 FROM FC_DirectoryLevelTree WHERE Parent=%d; " % (lPath,parentDirID) 
      result = self.db._query(req,conn)
      req = "UPDATE FC_DirectoryLevelTree SET %s=@tmpvar WHERE DirID=%d; " % (lPath,dirID)   
      result = self.db._update(req,conn)
      req = "UNLOCK TABLES;"
      result = self.db._query(req,conn)      
      if not result['OK']:
        return result
    return S_OK(dirID)
  
  def existsDir(self,path):
    """ Check the existence of a directory at the specified path
    """
    result = self.findDir(path)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_OK({"Exists":False})
    else:
      return S_OK({"Exists":True,"DirID":result['Value']})  
    
  def getParent(self,path):
    """ Get the parent ID of the given directory
    """  
  
    parent_dir = os.path.dirname(path)
    return self.findDir(parent_dir)
    
  def getParentID(self,dirPathOrID):
    """ Get the ID of the parent of a directory specified by ID
    """
    
    dirID = dirPathOrID
    if type(dirPathOrID) in StringTypes:
      result = self.findDir(dirPathOrID)
      if not result['OK']:
        return result
      dirID = result['Value']
    
    if dirID == 0:
      return S_ERROR('Root directory ID given')
    
    req = "SELECT Parent FROM FC_DirectoryLevelTree WHERE DirID=%d" % dirID
    result = self.db._query(req)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_ERROR('No parent found')
    
    return S_OK(result['Value'][0][0])
  
  def getDirectoryPath(self,dirID):
    """ Get directory name by directory ID
    """
    req = "SELECT DirName FROM FC_DirectoryLevelTree WHERE DirID=%d" % int(dirID)
    result = self.db._query(req)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_ERROR('Directory with id %d not found' % int(dirID) )
    
    return S_OK(result['Value'][0][0])
  
  def getDirectoryName(self,dirID):
    """ Get directory name by directory ID
    """
    
    result = self.getDirectoryPath(dirID)
    if not result['OK']:
      return result
    
    return S_OK(os.path.basename(result['Value']))
  
  def getPathIDs(self,path):
    """ Get IDs of all the directories in the parent hierarchy for a directory
        specified by its path
    """    
    
    elements = path.split('/')
    pelements = []
    dPath = ''
    for el in elements[1:]:
      dPath += '/'+el
      pelements.append(dPath)
      
    pathString = [ "'"+p+"'" for p in pelements ]
    req = "SELECT DirID FROM FC_DirectoryLevelTree WHERE DirName in (%s) ORDER BY DirID" % pathString
    result = self.db._query(req)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_ERROR('Directory %s not found' % path)
       
    return S_OK([ x[0] for x in result['Value'] ])
  
  def getPathIDsByID(self,dirID):
    """ Get IDs of all the directories in the parent hierarchy for a directory
        specified by its ID
    """
    
    # The method should be rather implemented using enumerated paths
    
    result = self.getDirectoryPath(dirID)
    if not result['OK']:
      return result
    dPath = result['Value']
    return self.getPathIDs(dPath)
    
  def getChildren(self,path):
    """ Get child directory IDs for the given directory 
    """  
    if type(path) in StringTypes:
      result = self.findDir(path)
      if not result['OK']:
        return result
      dirID = result['Value']
    else:
      dirID = path
        
    req = "SELECT DirID FROM FC_DirectoryLevelTree WHERE Parent=%d" % dirID
    result = self.db._query(req)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_OK([])
    
    return S_OK([ x[0] for x in result['Value'] ])
  
  def getSubdirectoriesByID(self,dirID,level=0):
    """ Get all the subdirectories of the given directory at a given level
    """
    
    if not level:
      req = "SELECT Level FROM FC_DirectoryLevelTree WHERE DirID=%d" % dirID
      result = self.db._query(req)
      if not result['OK']:
        return result
      if not result['Value']:
        return S_ERROR('Directory %d not found' % dirID)
      level = result['Value'][0][0]
    
    sPaths = []
    for i in range(1,level+1):
      sPaths.append('LPATH%d' % i)
    pathString = ','.join(sPaths)  
    req = "SELECT Level,DirID FROM FC_DirectoryLevelTree AS F1"
    req += " JOIN (SELECT %s FROM FC_DirectoryLevelTree WHERE DirID=%d) AS F2 ON " % (pathString,dirID)
    sPaths = []
    for i in range(1,level+1):
      sPaths.append('F1.LPATH%d=F2.LPATH%d' % (i,i))
    pString = ' AND '.join(sPaths)  
    req += "%s AND F1.Level > %d" % (pString,level)
    
    print req
    
    
    result = self.db._query(req)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_OK([])
    
    resDict = {}
    for row in result['Value']:
      resDict[row[1]] = row[0]
      
    return S_OK(resDict)
  
  def getSubdirectories(self,path):
    """ Get subdirectories of the given directory
    """    
    
    result = self.findDir(path)
    if not result['OK']:
      return result
    if not result['Value']:
      return S_OK({})
    
    dirID = result['Value']
    level = result['Level']
    
    result = self.getSubdirectoriesByID(dirID,level)
    return result
    
    