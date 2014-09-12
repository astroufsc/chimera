-----------------
Chimera Scheduler
-----------------

Chimera scheduler schedules and executes queued observations. It consists now of a series of softwares that help organize 
and execute autonomous observations of targets with the most different set of parameters and constraints. 

12/Set/2014: Current version still does not apply weather, moon, airmass and altitude constraints. Will add this 
capability soon, in order of importance.

Setting up ``chimera-addproject``
-------------------------
Before the scheduler can run properly the user must set several things. Specially full target list must be uploaded to the 
database, as well as information on observations constraints and properties (filters, exposure times, number of exposures). 

The scheduler works in an hierarchial way. Each scheduled observation must be part of a science project with a specific priority, 
which is devided in observing blocks, which is then devided in subblocks with observing targets. All this information is loaded
to the chimera database by the task chimera-addproject. 

We start by including projects to the database. To do that, you must create a text file (ascii) with the following format:

project.cfg


  [projects]
  
  pid = SPLUS 
  
  pi = Claudia Mendez de Oliveira
  
  abstract = Um texto super interessante sobre o SPLUS.
  
  url = www.splus.iag.usp.br
  
  priority = 1 
  
  [blockpar.0]

  id = 0

  pid = SPLUS

  maxairmass = 1.5
  
  maxmoonBright = 99.
  
  minmoonBright = 50.
  
  minmoonDist = -1
  
  maxseeing = 1.5
  
  cloudcover = 0.8
  
  schedalgorith = 0
  
  applyextcorr = 1
  
  [blockpar.1]
  
  id = 1
  
  pid = SPLUS
  
  maxairmass = 1.5
  
  maxmoonBright = 80.
  
  minmoonBright = 0.
  
  minmoonDist = -1
  
  maxseeing = 1.5
  
  cloudcover = 0.8
  
  schedalgorith = 0
  
  applyextcorr = 1
  
  [blockpar.3]
  
  id = 2
  
  pid = SPLUS
  
  maxairmass = 1.5
  
  maxmoonBright = 80.
  
  minmoonBright = 0.
  
  minmoonDist = -1
  
  maxseeing = 1.5
  
  cloudcover = 0.5
  
  schedalgorith = 0
  
  applyextcorr = 0 ::

Note that the first section of the configuration file ([projects]) is followed by some basic information 
on the project. The main informatin here is the priority of the project. Projects with priority = 0 are
scheduled in the main queue. This means that the program has time restriction and the project should be 
executed at some specified time. This should be avoided as much as possible. Use it for really high priority 
programs or programs with tight time constraints, like observations of ToOs and standard stars (that need be 
observed on specific airmasses with specific number of times). After that there are three subsections specifying 
the observation blocks of the project. Here you specify the enviromental constraint, observation constraint are 
deal with later.


Once in the database, the observations can than be scheduled and executed. 


Running ``chimera-sched``
-------------------------

Example: NoNoNo
---------------

``test`` preformatted text
