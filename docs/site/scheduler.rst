-----------------
Chimera Scheduler
-----------------

Chimera scheduler schedules and executes queued observations. It consists now of a series of softwares that help organize 
and execute autonomous observations of targets with the most different set of parameters and constraints. 

12/Set/2014: Current version still does not apply weather, moon, airmass and altitude constraints. Will add this 
capability soon, in order of importance.

Setting up with ``chimera-addproject``
--------------------------------------

Before the scheduler can run properly the user must set several things. Specially full target list must be uploaded to the 
database, as well as information on observations constraints and properties (filters, exposure times, number of exposures). 

The scheduler works in an hierarchial way. Each scheduled observation must be part of a science project with a specific priority, 
which is devided in observing blocks, which is then devided in subblocks with observing targets. All this information is loaded
to the chimera database by the task chimera-addproject. 

We start by including targets to the database. Here are two examples of text files that can be used to load targets to the 
database:

smaps_tiles.dat::

  SMAPS,SMAPS_00001,23 59 60.00,-10 44 31.20
  SMAPS,SMAPS_00002,23 55 25.00,-10 43 51.11
  SMAPS,SMAPS_00003,23 50 50.13,-10 41 50.86
  SMAPS,SMAPS_00004,23 46 15.51,-10 38 30.55
  SMAPS,SMAPS_00005,23 41 41.28,-10 33 50.37
  .
  .
  .
  SMAPS,SMAPS_04331,10 18 36.41,-24 05 59.29
  SMAPS,SMAPS_04332,10 12 30.91,-23 41 44.82
  SMAPS,SMAPS_04333,10 06 27.48,-23 16 46.68
  SMAPS,SMAPS_04334,10 00 26.15,-22 51 06.18
  SMAPS,SMAPS_04335,10 04 35.69,-24 40 11.83


landolt1992.txt::

  STD,TPHE A     ,00:30:09,-46:31:22,2000.,14.651
  STD,TPHE B     ,00:30:16,-46:27:55,2000.,12.334
  STD,TPHE C     ,00:30:17,-46:32:34,2000.,14.376
  STD,TPHE D     ,00:30:18,-46:31:11,2000.,13.118
  .
  .
  .
  STD,115 268    ,23:42:30,+00:52:11,2000.,12.494
  STD,115 420    ,23:42:36,+01:05:58,2000.,11.161
  STD,115 271    ,23:42:41,+00:45:10,2000., 9.695
  STD,115 516    ,23:44:15,+01:14:13,2000.,10.434
  STD,PG2349+002 ,23:51:53,+00:28:17,2000.,13.277

The first column specify a project ID, a unique string that identify the project which the target is part of. This is actually not
used by the scheduler, as you can have a single target that is part of multiple projects. Instead we use a different way to link
each target. We will clarify this furthermore. The second column is the name of the target followed by RA and Dec and, optionally,
Epoch and magnitude. If no Epoch is given, the program will assume J2000. 

To include the targets to the database use:

  chimera-addproject --newTargetsDB -f smaps_tiles.dat # This will clean the target database before entryng new targets

and 

  chimera-addproject --addTargetsDB -f landolt1992.txt # This adds targets to the database

Now we include projects to the database. To do that, you must create a text file (ascii) with the following format:

project.cfg::


  [projects]
  pid = SPLUS 
  pi = Claudia Mendes de Oliveira
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
  applyextcorr = 0

project_std.cfg:: 

  [projects]
  
  pid = EXTMONI
  pi = Claudia Mendez de Oliveira
  abstract = Extinction monitoring.
  url = www.splus.iag.usp.br
  priority = 0
  
  [blockpar.0]
  
  id = 0
  pid = EXTMONI
  maxairmass = -1.
  maxmoonBright = 99.
  minmoonBright =  0.
  minmoonDist = 40.
  maxseeing = 2.5
  cloudcover = 0.8
  schedalgorith = 1
  applyextcorr = 1

Note that the first section of the configuration file (``[projects]``) is followed by some basic information 
on the project. The main informatin here is the priority of the project. Projects with ``priority = 0`` are
scheduled in the main queue. This means that the program has time restriction and the project should be 
executed at some specified time. This should be avoided as much as possible. Use it for really high priority 
programs or programs with tight time constraints, like observations of ToOs and standard stars (that need be 
observed on specific airmasses with specific number of times). After that there are three subsections specifying 
the observation blocks of the project. Here you specify the enviromental constraint, observation constraint are 
deal with later.

The final step is to entry observation block information to the database. To do this you first need to check the ID of each 
target in the database. We will use this to link since it is a unique identification for each target. If you follow the same 
order as we showed before than you must have something like this in the target database:

sqlite> select * from targets; ::

  id          objname      type        lastObservation  targetRa    targetDec   targetEpoch  targetMag   magFilter 
  ----------  -----------  ----------  ---------------  ----------  ----------  -----------  ----------  ----------
  1           SMAPS_00001  SMAPS                        24.0        -10.742     2000.0       0.0                   
  2           SMAPS_00002  SMAPS                        23.9236111  -10.730863  2000.0       0.0                   
  3           SMAPS_00003  SMAPS                        23.8472583  -10.697461  2000.0       0.0                   
  4           SMAPS_00004  SMAPS                        23.770975   -10.641819  2000.0       0.0                   
  5           SMAPS_00005  SMAPS                        23.6948     -10.563991  2000.0       0.0                   
  .
  .
  .
  4331        SMAPS_04331  SMAPS                        10.3101138888889  -24.0998027777778  2000.0       0.0                   
  4332        SMAPS_04332  SMAPS                        10.2085861111111  -23.6957833333333  2000.0       0.0                   
  4333        SMAPS_04333  SMAPS                        10.1076333333333  -23.2796333333333  2000.0       0.0                   
  4334        SMAPS_04334  SMAPS                        10.0072638888889  -22.8517166666667  2000.0       0.0                   
  4335        SMAPS_04335  SMAPS                        10.0765805555556  -24.6699527777778  2000.0       0.0                   
  4336        TPHE A       STD                          0.5025            -46.5227777777778  2000.0       14.651                
  4337        TPHE B       STD                          0.50444444444444  -46.4652777777778  2000.0       12.334                
  4338        TPHE C       STD                          0.50472222222222  -46.5427777777778  2000.0       14.376                
  4339        TPHE D       STD                          0.505             -46.5197222222222  2000.0       13.118                
  4340        TPHE E       STD                          0.50527777777777  -46.41             2000.0       11.63                 
  . 
  .
  .
  4857        115 268      STD                          23.7083333  0.86972222  2000.0       12.494                
  4858        115 420      STD                          23.71       1.09944444  2000.0       11.161                
  4859        115 271      STD                          23.7113888  0.75277777  2000.0       9.695                 
  4860        115 516      STD                          23.7375     1.23694444  2000.0       10.434                
  4861        PG2349+002   STD                          23.8647222  0.47138888  2000.0       13.277                

After checking this out, you need to create a list of observing blocks with the following format:

obsblock.lis ::

  SPLUS   00001 00001 splus_block.cfg 0
  SPLUS   00002 00002 splus_block.cfg 0
  SPLUS   00003 00003 splus_block.cfg 0
  SPLUS   00004 00004 splus_block.cfg 0
  SPLUS   00005 00005 splus_block.cfg 0
  .
  .
  .
  SPLUS   04331 04331 splus_block.cfg 0
  SPLUS   04332 04332 splus_block.cfg 0
  SPLUS   04333 04333 splus_block.cfg 0
  SPLUS   04334 04334 splus_block.cfg 0
  SPLUS   04335 04335 splus_block.cfg 0
  EXTMONI 00001 04336 stdblock.cfg    0
  EXTMONI 00002 04337 stdblock.cfg    0
  EXTMONI 00003 04338 stdblock.cfg    0
  EXTMONI 00004 04339 stdblock.cfg    0
  EXTMONI 00005 04340 stdblock.cfg    0
  EXTMONI 00006 04341 stdblock.cfg    0
  .
  .
  .
  EXTMONI 00522 04857 stdblock.cfg    0
  EXTMONI 00523 04858 stdblock.cfg    0
  EXTMONI 00524 04859 stdblock.cfg    0
  EXTMONI 00525 04860 stdblock.cfg    0
  EXTMONI 00526 04861 stdblock.cfg    0
  EXTMONI 00527 04862 stdblock.cfg    0

The first column is the project ID of which this block is part of. The second columns is the block number and the third the
object id in the target database. Note how the block number runs from 1 to 43335 for project SPLUS and then goes back to 1 when
we go to project EXTMONI, while the object id keeps increasing. Also, here we create a single block for each target. This is 
usually the case for normal observations. But, in some cases, a single block may have more than one target. If this happens just 
repeate the block number (second column) with different object id. Note however that to deal with this, specific scheduling 
algorithms must be implemented. Depending of what you want the scheduler will not deal with this properly yet. Here you can also 
note that a single object can be part of different projects. Just by selecting the appropriate values for columns 1 and 2 and 
then repeating column 3. Column 4 of this file specify the observations configuration of each block and the last column 
specify which kind of block it is (the subsections, specifying the enviromental constraints in the project configuration file).

The observations configuration file must have the following (self explanatory) format:

splus_block.cfg ::

  [blockconfig]
  
  filter = B,V,R,I
  exptime = 80.,80.,60.,40.
  nexp = 2,1,1,2
  imagetype=OBJECT,OBJECT,OBJECT,OBJECT


and 

stdblock.cfg ::

  [blockconfig]
  filter = B,V,R,I
  exptime = 5.,5.,5.,5.
  nexp = 1,1,1,1
  imagetype=OBJECT,OBJECT,OBJECT,OBJECT


Note how you have/can specify the imagetype of the observation in each filter. If you need to take darks or bias during an
observation or schedule skyflats, the scheduler can deal with it properly. 

To add the observation blocks to the database you can just run:

  chimera-addproject --addObsBlock -f obsblock.lis 

After this information is loaded to the database, observations can then be scheduled and executed. 


Running ``chimera-sched``
-------------------------

WORK IN PROGRESS...


Example: NoNoNo
---------------

``test`` preformatted text
