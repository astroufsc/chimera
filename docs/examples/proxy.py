
from chimera.core.chimera  import chimera
from chimera.core.proxy    import Proxy
from chimera.core.cmanager import Manager

# create a new manager (this is a singleton, so only one
# copy will be created even if you call Manager() again)

manager = Manager()

#
# 1. Adding objects and getting a proxy
# 

# just add a fake Telescope class (returns a valid proxy)
tel = manager.start ("/Telescope/fake")

# synchronous "slew" (this will trigger slewComplete and our slew_cb will be called
tel.slew ("ra", "dec")

# asynchronous "slew"
tel.slew.begin ("ra", "dec")

# get remote configuration
print "[config] slew_rate:", tel["slew_rate"]


#
# 2. There are other ways to get proxy
#

# from manager (this ensure that the object exists on the manager, see ChimeraProxy below)
tel = manager.getProxy ("/Telescope/fake")
tel.slew ("ra", "dec")

# if you don't know the name of the instance no problem, pass an index starting with 0
tel = manager.getProxy ("/Telescope/0")
tel.slew ("ra", "dec")

#
# 3. Proxies for remote objects
# now, if you want a proxy for an object running on ther server?
# manager are local bounded objects, and manages only local objects,
# to get Proxy for another objects, there are 2 options:
#

#
# 3. Chimera obejcts (this works for local objects too)
# this method talks to the objects manager before, to ensure
# that the object exists on the manager side (again, see ChimeraProxy below)
#

tel = chimera.Telescope("fake", host='localhost')
tel.slew ("ra", "dec")

# this will use index as no name was passed
tel = chimera.Telescope(host='localhost')
tel.slew ("ra", "dec")

#
# 3. 2. ChimeraProxy objects.
# this is the low level proxy used by the system. They will try to contact
# the object directly, bypassing manager. So, if the object was not
# created by the manager, this will raise an exception (the syntax is the same as above)
#

# proxy without manager interface (fastest, don't ask manager about it)
tel = Proxy ("/Telescope/fake")
tel.slew ("ra", "dec")

tel = Proxy ("/Telescope/0")
tel.slew ("ra", "dec")

tel = Proxy ("/Telescope/fake", host = 'localhost')
tel.slew ("ra", "dec")

tel = Proxy ("/Telescope/0",    host = 'localhost')
tel.slew ("ra", "dec")

# OK, enough proxies, but they are REALLY important, its the ONLY way to get an object,
# so you really need to know how to get them.

