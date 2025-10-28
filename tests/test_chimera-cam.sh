#!/bin/bash
set -xe
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --version
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose -n 2 -t 2 -i 3 -o '$DATE-$TIME.fits' -f R --shutter=open
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose --shutter=close --object=Test
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose --shutter=leave --binning=BINNING 2x2 
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose --subframe=1:5,1:5 --compress=gzip
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose --subframe=1:5,1:5 --compress=zip
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose --subframe=1:5,1:5 --compress=bz2
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --expose --subframe=1:5,1:5 --compress=fits_rice --ignore-dome 
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --force-display
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v -T -1 
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v -w --expose
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --start-fan
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --stop-cooling
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --stop-fan
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v -F
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --info
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --bias
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --flat
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --sky-flat
chimera-cam -vv --camera 127.0.0.1:9000/Camera/0 -v --dark -t2
