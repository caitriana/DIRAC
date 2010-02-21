""" The Propagation_Policy module is a policy module used to update the status of
    a validRes, based on statistics of its services (for the site), 
    of its nodes (for the services), or of its SE (for the Storage services). 
"""

from DIRAC.ResourceStatusSystem.Policy.PolicyBase import PolicyBase
from DIRAC.ResourceStatusSystem.Client.Command.MacroCommand import MacroCommand
from DIRAC.ResourceStatusSystem.Utilities.Exceptions import *
from DIRAC.ResourceStatusSystem.Utilities.Utils import *

class Propagation_Policy(PolicyBase):
  
  def evaluate(self, args, commandIn=None, knownInfo=None):
    """ Propagation policy on Site or Service, using args (tuple).
        It will get Services or nodes or SE stats. 
        
        :params:
          :attr:`args`: a tuple
            `args[0]` string, should be a ValidRes
           
            `args[1]` string, should be the name of the ValidRes

            `args[2]` string, should be the present status
          
            `args[3]` string, should be a ValidRes from which 
            I want to propagate from (Service, Resource or StorageElement)

          :attr:`commandIn`: optional command object
          
          :attr:`knownInfo`: optional information dictionary
        
        :returns:
            { 
              `SAT`:True|False, 
              `Status`:Active|Probing|Banned, 
              `Reason`:'A:X/P:Y/B:Z'
            }
    """ 

    if not isinstance(args, tuple):
      raise TypeError, where(self, self.evaluate)
    
    if args[2] not in ValidStatus:
      raise InvalidStatus, where(self, self.evaluate)

    #get stats
    if knownInfo is not None and 'stats' in knownInfo.keys():
      stats = knownInfo['stats']
    else:
      if commandIn is not None:
        command = commandIn
      else:
        # use standard Commands 
        if args[3] in ('Service', 'Services'):
          from DIRAC.ResourceStatusSystem.Client.Command.RS_Command import ServiceStats_Command
          command = ServiceStats_Command()
        elif args[3] in ('Resource', 'Resources'):
          from DIRAC.ResourceStatusSystem.Client.Command.RS_Command import ResourceStats_Command
          command = ResourceStats_Command()
        elif args[3] in ('StorageElement', 'StorageElements'):
          from DIRAC.ResourceStatusSystem.Client.Command.RS_Command import StorageElementsStats_Command
          command = StorageElementsStats_Command()
        else:
          raise InvalidRes, where(self, self.evaluate)
    
      res = command.doCommand((args[0], args[1]))
      
      stats = res['stats']
    
    if stats is None:
      return {'SAT':None}
    
    values = []
    val = (100 * stats['Active'] + 50 * stats['Probing']) / stats['Total']
    
    if val == 100:
      status = 'Active'
    elif val == 0:
      status = 'Banned'
    else:
      status = 'Probing'
      
    result = {}
    
    if args[2] == 'Active':
      if status == 'Active':
        result['SAT'] = False
        result['Status'] = 'Active'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
      if status == 'Probing':
        result['SAT'] = True
        result['Status'] = 'Probing'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
      if status == 'Banned':
        result['SAT'] = True
        result['Status'] = 'Banned'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
       
    elif args[2] == 'Probing':
      if status == 'Active':
        result['SAT'] = True
        result['Status'] = 'Active'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
      if status == 'Probing':
        result['SAT'] = False
        result['Status'] = 'Probing'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
      if status == 'Banned':
        result['SAT'] = True
        result['Status'] = 'Banned'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
        
    elif args[2] == 'Banned':
      if status == 'Active':
        result['SAT'] = True
        result['Status'] = 'Active'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
      if status == 'Probing':
        result['SAT'] = True
        result['Status'] = 'Probing'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
      if status == 'Banned':
        result['SAT'] = False
        result['Status'] = 'Banned'
        result['Reason'] =  'Stats %s: A:%d/P:%d/B:%d' %(args[3], 
                                                        stats['Active'], 
                                                        stats['Probing'], 
                                                        stats['Banned'])
        
    
    return result