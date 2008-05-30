from chimera.core.manager import Manager

manager = Manager(host='localhost', port=8000)
manager.addLocation("/Example1/example", start=True)

manager.wait()
