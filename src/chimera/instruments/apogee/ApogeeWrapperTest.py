#!/usr/bin/python

from ApogeeWrapper import ApogeeManager
import datetime

now = datetime.datetime.now()

manager = ApogeeManager( "/tmp/python_image_test_" + now.strftime("%Y%m%d%H%M%S") + ".xxx" )
manager.setUp()
manager.run()
manager.stop()