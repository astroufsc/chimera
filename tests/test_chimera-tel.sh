#!/bin/bash
set -xe
chimera-tel -v --version
chimera-tel -v -h
chimera-tel -v --info
chimera-tel -v -q
chimera-tel -v --slew --ra 10 --dec -10 --epoch 2001.1
chimera-tel -v --sync --ra 10 --dec -10 --epoch 2001.1
chimera-tel -v --slew --az 1 --alt 60
chimera-tel -v --slew --object NGC4755
chimera-tel -v --sync --object NGC4755
chimera-tel -v --slew --ra 12:53:39.600 --dec "-60:22:15.600"
chimera-tel -v --slew --object bla_bla
chimera-tel -v --rate=0.1 -E 1
chimera-tel -v --rate=0.1 -N 2
chimera-tel -v --rate=0.1 -S 3
chimera-tel -v --rate=0.1 -W 4
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
