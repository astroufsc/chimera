#!/bin/bash
set -xe
chimera-dome -v --version
chimera-dome -v --fan-on
chimera-dome -v --fan-speed=100
chimera-dome -v --fan-off
chimera-dome -v --track
chimera-dome -v --stand
chimera-dome -v --light-on
chimera-dome -v --light-intensity=100
chimera-dome -v --light-off
chimera-dome -v --info
chimera-dome -v --to=89
chimera-dome -v --close-flap
chimera-dome -v --close-slit
chimera-dome -v --open-slit
chimera-dome -v --open-flap
