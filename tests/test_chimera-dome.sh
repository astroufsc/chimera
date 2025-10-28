#!/bin/bash
set -xe
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --version
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --fan-on
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --fan-speed=100
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --fan-off
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --track
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --stand
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --light-on
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --light-intensity=100
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --light-off
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --info
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --to=89
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --close-flap
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --close-slit
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --open-slit
chimera-dome --dome 127.0.0.1:9000/Dome/0 -v --open-flap
