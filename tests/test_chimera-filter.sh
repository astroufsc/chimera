#!/bin/bash
set -xe
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv --version
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv -h
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv -F
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv --info
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv -f U
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv -f B
chimera-filter --wheel 127.0.0.1:9000/Camera/0 -vv --get-filter
