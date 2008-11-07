########################################################################
# $Id: SandboxHandler.py,v 1.12 2008/11/07 11:10:07 atsareg Exp $
########################################################################

""" SandboxHandler is the implementation of the Sandbox service
    in the DISET framework

    The following methods are available in the Service interface

    submitJob()
    rescheduleJob()

"""

__RCSID__ = "$Id: SandboxHandler.py,v 1.12 2008/11/07 11:10:07 atsareg Exp $"

from types import *
from DIRAC.Core.DISET.RequestHandler import RequestHandler
from DIRAC import gLogger, S_OK, S_ERROR
from DIRAC.ConfigurationSystem.Client.Config import gConfig
from DIRAC.WorkloadManagementSystem.DB.SandboxDB import SandboxDB
from DIRAC.WorkloadManagementSystem.DB.JobDB import JobDB

# This is a global instance of the JobDB class
sandboxDB = False
jobDB = False
sandbox_type = "Unknown"

def initializeSandboxHandler(serviceInfo):

  global sandboxDB
  global jobDB
  global sandbox_type

  sandbox = serviceInfo["serviceName"].split('/')[1]
  if sandbox == "InputSandbox" or sandbox == "OutputSandbox":
    sandbox_type = sandbox
  else:
    return S_ERROR('Unknown sandbox service '+sandbox_type)

  sandboxDB = SandboxDB(sandbox_type)
  jobDB = JobDB()
  return S_OK()

class SandboxHandler(RequestHandler):

  def __parsefileID(self, fileID):
    """ Parse the file ID string to extract job metadata, e.g. jobID
    """

    ind = fileID.find('::')
    if ind == -1:
      return S_ERROR("Can not get the JobID")

    try:
      jobID = int(fileID[:ind])
      fname = fileID[ind+2:]
    except Exception, x:
      return S_ERROR("Can not get the JobID")

    return S_OK((jobID,fname))

  def transfer_fromClient( self, fileID, token, fileSize, fileHelper ):
    """ Method to receive bytes from clients.
        fileSize can be Xbytes or -1 if unknown.
    """

    result = self.__parsefileID(fileID)
    if not result['OK']:
      return result

    jobID,fname = result['Value']

    result = fileHelper.networkToString()
    if result['OK']:
      fileString = result['Value']
      gLogger.info('Received file %s of size %d for job %d' %
                   (fname,len(fileString), jobID))
    else:
      return result


    inFields = ['JobID','FileName','FileBody']
    inValues = [jobID,fname,fileString]

    result = sandboxDB._insert(sandbox_type,inFields,inValues)
    if not result['OK']:
      if result['Message'].find('Duplicate entry') != -1:
        return S_ERROR('InputSandbox file %s for job %d already exists' % (fname,jobID))
    return result

  def transfer_bulkFromClient( self, fileID, token, fsize, fileHelper ):
    """ Receive files packed into a tar archive by the fileHelper logic.
        token is used for access rights confirmation.
    """

    result = self.__parsefileID(fileID)
    if not result['OK']:
      return result

    jobID,fname = result['Value']

    result = fileHelper.networkToString()
    if result['OK']:
      fileString = result['Value']
      gLogger.info('Received file %s of size %d for job %d' %
                   (fname,len(fileString), jobID))
    else:
      return result

    result = sandboxDB.storeFile(jobID,fname,fileString,sandbox_type)
    if not result['OK']:
      if result['Message'].find('Duplicate entry') != -1:
        return S_ERROR('InputSandbox file %s for job %d already exists' % (fname,jobID))
      return result
    return S_OK()

  def transfer_toClient( self, fileID, token, fileHelper ):
    """ Method to send bytes to clients.
    """

    result = self.__parsefileID(fileID)
    if not result['OK']:
      return result

    jobID,fname = result['Value']

    result = sandboxDB.getSandboxFile(jobID,fname,sandbox_type)
    if not result['OK']:
      return result
    fileString = result['Value']      
 
    result = fileHelper.stringToNetwork(fileString)

    if not fileString:
      return S_ERROR('File not found')

    if result['OK']:
      gLogger.info('Sent file %s of size %d' % (fileID,len(fileString)))
    else:
      return result

    return S_OK()

  types_setSandboxReady = [ IntType ]
  def export_setSandboxReady(self,jobID):
    """  Set the sandbox ready for the job with jobID
    """

    return jobDB.setSandboxReady(jobID,sandbox_type)

  types_getFileNames = [ IntType ]
  def export_getFileNames(self,jobID):
    """ Remove sandbox for the given job
    """

    return sandboxDB.getFileNames(jobID,sandbox_type)

  types_removeSandbox = [ IntType ]
  def export_removeSandbox(self,jobID):
    """ Remove sandbox for the given job
    """

    return sandboxDB.removeSandbox(jobID,fname,sandbox_type)

  types_getSandboxStats = []
  def export_getSandboxStats(self):
    """ Get sandbox statistics
    """
    result = sandboxDB.getSandboxStats(sandbox_type)
    return result

