
from chimera.core.main     import chimera
from chimera.core.proxy    import Proxy
from chimera.core.manager  import Manager

# our example object
from minimo import Minimo


# create a new manager (default host (localhost), defaulr port 7666 or try next 4 from default)
manager = Manager()

#
# 1. Adding objects and getting a proxy
# 

# just add a min Minimoescope class (returns a valid proxy)
minimo = manager.addClass(Minimo, "min", start=True)

# synchronous "doFoo"
minimo.doFoo ("ra dec")

#
# 2. There are other ways to get proxy
#

# from manager (this ensure that the object exists on the manager, see ChimeraProxy below)
minimo = manager.getProxy ("/Minimo/min")
minimo.doFoo ("ra dec")

# if you don't know the name of the instance no problem, pass an index starting with 0
minimo = manager.getProxy ("/Minimo/0")
minimo.doFoo ("ra dec")

minimo = manager.getProxy (Minimo, "min")
minimo.doFoo ("ra dec")

# if you don't know the name of the instance no problem, pass an index starting with 0
minimo = manager.getProxy (Minimo)
minimo.doFoo ("ra dec")

minimo = manager.getProxy (Minimo, host="localhost", port=9090)
minimo.doFoo ("ra dec")

minimo = manager.getProxy ("localhost:9090/Minimo/0")
minimo.doFoo ("ra dec")

#
# 3. Proxies for remote objects
# now, if you want a proxy for an object running on other server?
# manager are local bounded objects, and manages only local objects,
# to get Proxy for another objects, there are 2 options:
#

#
# 3. Chimera obejcts (this works for local objects too)
# this method talks to the objects manager before, to ensure
# that the object exists on the manager side (again, see ChimeraProxy below)
#

minimo = chimera.Minimo("min", host='localhost')
minimo.doFoo ("ra dec")

# this will use index as no name was passed
minimo = chimera.Minimo(host='localhost')
minimo.doFoo ("ra dec")

#
# 3. 2. ChimeraProxy objects.
# this is the low level proxy used by the system. They will try to contact
# the object directly, bypassing manager. So, if the object was not
# created by the manager, this will raise an exception (the syntax is the same as above)
#

# proxy without manager interface (fastest, don't ask manager about it)
minimo = Proxy ("/Minimo/min")
minimo.doFoo ("ra dec")

minimo = Proxy ("/Minimo/0")
minimo.doFoo ("ra dec")

minimo = Proxy ("/Minimo/min", host = 'localhost')
minimo.doFoo ("ra dec")

minimo = Proxy ("/Minimo/0", host = 'localhost')
minimo.doFoo ("ra dec")

# OK, enough proxies, they are REALLY important, its the ONLY way to get an object,
# so you really need to know how to get them.

manager.shutdown()
