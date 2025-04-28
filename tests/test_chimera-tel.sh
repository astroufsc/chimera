#!/bin/bash
set -xe
chimera-tel -v --version
chimera-tel -v -h
chimera-tel -v --info
chimera-tel -v --sync
chimera-tel -v -q
chimera-tel -v --slew --ra 10 --dec -10 --epoch J2001.1
chimera-tel -v --slew --az 0 --alt 60
chimera-tel -v --slew --object M42
chimera-tel -v --rate=MAX -E 1
chimera-tel -v --rate=CENTER -N 2
chimera-tel -v --rate=FIND -S 3
chimera-tel -v --rate=GUIDE -W 4
chimera-tel -v --init
chimera-tel -v --park
chimera-tel -v --unpark
chimera-tel -v --close-cover
chimera-tel -v --open-cover
chimera-tel -v --side-east
chimera-tel -v --side-west
chimera-tel -v --start-tracking
chimera-tel -v --stop-tracking
chimera-tel -v --fan-speed=50
chimera-tel -v --fan-on
chimera-tel -v --fan-off
