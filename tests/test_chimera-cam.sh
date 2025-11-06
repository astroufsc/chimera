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
chimera-cam -v --expose --force-display
chimera-cam -v -T -1 
chimera-cam -v --start-fan
chimera-cam -v --stop-cooling
chimera-cam -v --stop-fan
chimera-cam -v -F
chimera-cam -v --info
chimera-cam -v --expose --bias
chimera-cam -v --expose --flat
chimera-cam -v --expose --sky-flat
chimera-cam -v --expose --dark -t2

# open dome slit, slew telescope, take an exposure
chimera-dome --open-slit --track && \
chimera-tel --slew --az 10 --alt 60 && \
chimera-cam -v -w --expose 
