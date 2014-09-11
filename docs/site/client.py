from chimera.core.manager import Manager

manager = Manager()

example = manager.getProxy("localhost:8000/Example1/example")
example.doSomething("client argument")
