#!/bin/bash
set -xe
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --version
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v -h
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --info
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --slew --ra 10 --dec -10 --epoch 2000
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --sync --ra 10 --dec -10 --epoch 2000
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --slew --az 1 --alt 60
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --slew --object NGC4755
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --sync --object NGC4755
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --slew --ra 12:53:39.600 --dec "-60:22:15.600"
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --slew --object bla_bla
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --rate=0.1 -E 1
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --rate=0.1 -N 2
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --rate=0.1 -S 3
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --rate=0.1 -W 4
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --park
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --unpark
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --close-cover
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --open-cover
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --side-east
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --side-west
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --start-tracking
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --stop-tracking
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --fan-speed=50
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --fan-on
chimera-tel --telescope 127.0.0.1:9000/Telescope/0 -v --fan-off
