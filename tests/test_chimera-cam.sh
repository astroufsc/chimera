#!/bin/bash
set -xe
chimera-cam -vvvvv --version
chimera-cam -vvvvv --expose -n 2 -t 2 -i 3 -o '$DATE-$TIME.fits' -f R --shutter=open
chimera-cam -vvvvv --expose --shutter=close --object=Test
chimera-cam -vvvvv --expose --shutter=leave --binning=BINNING 2x2 
chimera-cam -vvvvv --expose --subframe=1:5,1:5 --compress=gzip
chimera-cam -vvvvv --expose --subframe=1:5,1:5 --compress=zip
chimera-cam -vvvvv --expose --subframe=1:5,1:5 --compress=bz2
chimera-cam -vvvvv --expose --subframe=1:5,1:5 --compress=fits_rice --ignore-dome 
chimera-cam -vvvvv --force-display
chimera-cam -vvvvv -T -1 
chimera-cam -vvvvv -w --expose
chimera-cam -vvvvv --start-fan
chimera-cam -vvvvv --stop-cooling
chimera-cam -vvvvv --stop-fan
chimera-cam -vvvvv -F
chimera-cam -vvvvv --info
chimera-cam -vvvvv --bias
chimera-cam -vvvvv --flat
chimera-cam -vvvvv --sky-flat
chimera-cam -vvvvv --dark -t2
