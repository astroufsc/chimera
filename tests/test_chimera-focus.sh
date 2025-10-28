#!/bin/bash
set -xe
chimera-focus -vv --focuser 127.0.0.1:9000/Focuser/0 --version
chimera-focus -vv --focuser 127.0.0.1:9000/Focuser/0 -h
chimera-focus -vv --focuser 127.0.0.1:9000/Focuser/0 --to=1000
chimera-focus -vv --focuser 127.0.0.1:9000/Focuser/0 --info
chimera-focus -vv --focuser 127.0.0.1:9000/Focuser/0 --in=100
chimera-focus -vv --focuser 127.0.0.1:9000/Focuser/0 --out=100
