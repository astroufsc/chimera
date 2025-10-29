#!/bin/bash
set -xe
chimera-cam -v --version
chimera-cam -v --expose -n 2 -t 2 -i 3 -o '$DATE-$TIME.fits' -f R --shutter=open
chimera-cam -v --expose --shutter=close --object=Test
chimera-cam -v --expose --shutter=leave --binning=BINNING 2x2 
chimera-cam -v --expose --subframe=1:5,1:5 --compress=gzip
chimera-cam -v --expose --subframe=1:5,1:5 --compress=zip
chimera-cam -v --expose --subframe=1:5,1:5 --compress=bz2
chimera-cam -v --expose --subframe=1:5,1:5 --compress=fits_rice --ignore-dome 
chimera-cam -v --force-display
chimera-cam -v -T -1 
chimera-cam -v -w --expose
chimera-cam -v --start-fan
chimera-cam -v --stop-cooling
chimera-cam -v --stop-fan
chimera-cam -v -F
chimera-cam -v --info
chimera-cam -v --bias
chimera-cam -v --flat
chimera-cam -v --sky-flat
chimera-cam -v --dark -t2
