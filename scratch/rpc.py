def event(func):
    return func


class Manager:

    def register(self, cls, name):
        pass


class Object:

    def method(self): ...

    @event
    def event(self): ...


class Proxy:

    def __init__(self, address):
        self.address = address


# server-side: registry, lifecycle and requests handling
m = Manager()
m.register(Object, "name")


# local objects could use a faster path, like a direct call
# Proxies could share connections and be thread-safe
# Proxies should not be pickable, they should be created on the fly and will reuse connection if possible
# Proxies should be able to handle events, like a subscription to a topic
# Proxies should be able to handle async I/O, like a Future
# Proxies should be able to handle timeouts
# Proxies should be able to handle retries
# Proxies should be able to handle errors

# using a Proxy in a distributed systems is I/O, every call is I/O, so the same
# concerns of async I/O apply here.

# there must be a connection associated with the Proxy
p = Proxy("127.0.0.1:8088/Object/name")

# synchronous call, blocks until return or timeout (how to configure timeout?)
p.method()


async def foo():
    # asynchronous call, returns immediately and will block once .result is invoked
    fut = p.method.begin()
    fut.result()

    # asynchronous call, yield immediatelly and will continue once polled
    await p.method()


p.event += lambda: print("event")

# we need some way of handling events, like a loop,
# but we could have this in the backgroun by some kind of thread or async loop

# this is equivalent to the pure client example in Ice.
