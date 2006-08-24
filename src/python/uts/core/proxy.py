#! /usr/bin/python
# -*- coding: iso8859-1 -*-


import logging
import threading

from uts.core.async import AsyncResult

class Proxy(object):

    def __init__(self, obj, threadPool = None):

        self._obj = obj
        self._pool = threadPool

    def __getattribute__(self, value):
        obj = object.__getattribute__(self, '_obj')
        pool = object.__getattribute__(self, '_pool')

        if(hasattr(obj, value)):
            prop = getattr(obj, value)

# 			if(callable(prop) and hasattr(prop, "event")):
# 				return AsyncEvent(prop, pool)

            if(callable(prop)):
                return AsyncResult(prop, pool)

            # non callable, just returns
            return prop
        else:
            raise AttributeError

def lock(func):
	func.lock = threading.Lock()
	return func


if __name__ == '__main__':

    import time
    import threading
    
    from uts.core.threads import ThreadPool

    class Simples(object):

        def __init__(self):
            self.coisa = "haha"

        def nome(self):
            print "nome:", threading.currentThread().getName()
            return "nome: result (" + threading.currentThread().getName() + ")"

        def outroNome(self):
            time.sleep(5)
            print "outroNome:", threading.currentThread().getName()
            return "outroNome: result("+threading.currentThread().getName()+")"

        def nomeCallback(self, result):
            print "callback:", result


    try:

        pool = ThreadPool(5)

        p1 = Proxy(Simples(), pool)

        # calls nome synchronously in the main thread
        r1 = p1.nome()
        print r1

        # calls nome asynchronously in a new thread, will
		# call p1.nomeCallback when nome finishes
        r2 = p1.nome.begin(callback=p1.nomeCallback)

        # calls outroNome asynchronously in a new thread
        r3 = p1.outroNome.begin()

        # block until r3 (nome) ends
        print r3.end()

        print p1.coisa

    finally:
        pool.joinAll()

