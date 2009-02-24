import yaml

class ChimeraSchedulerObject(yaml.YAMLObject, list):
   yaml_flow_style = False
   innerName = 'actions'

   def appendList(self, list):
       for o in list:
           self.append(o)

   def __getstate__(self):
       d = self.__dict__.copy()
       #d.pop('innerName')
       d[self.innerName] = list(self)
       return d

   def __setstate__(self, d):
       toAppend = d.pop(self.__class__.innerName, None)
       if toAppend:
           self.appendList(toAppend)
       for k in d:
           self.__setattr__(k, d[k])

class ChimeraSchedulerAction(yaml.YAMLObject, object):
   yaml_flow_style = False

class Program(ChimeraSchedulerObject):

   yaml_tag=u'!program'
   innerName = 'observations'

   def __init__(self, name = 'Name', pi = 'Anonymous Observer',
                observations = []):
       list.__init__(self)
       self.name = name
       self.pi = pi
       self.appendList(observations)

class Observation(ChimeraSchedulerObject):
   yaml_tag = u'!observation'

   def __init__(self, notes='', actions = []):
       self.notes = notes
       self.appendList(actions)

class Unit(ChimeraSchedulerObject):
   yaml_tag = u'!observation'

   def __init__(self, notes='', actions = []):
       self.notes = notes
       self.appendList(actions)

class Focus(ChimeraSchedulerAction):
   yaml_tag = u'!focus'

   def __init__(self, target = False):
       self.target = target
       pass

if __name__ == '__main__':

    obs = [
        Observation('noActions'),
        Observation('WithFocus', [Focus()])
        ]
    p = Program('Calibration', observations=obs)
    print yaml.dump([p])

# =========================
#     - !program
#         name: Calibration
#         observations:
#         - !observation
#             actions: []
#             notes: noActions
#         - !observation
#             actions:
#             - !focus
#                 target: false
#             notes: WithFocus
#         pi: Anonymous Observer

#     =======================

