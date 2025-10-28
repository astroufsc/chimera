#!/bin/bash
set -xe
chimera-weather -vv -weatherstation 127.0.0.1:9000/WeatherStation/0 -t 0 -i
chimera-weather -vv -weatherstation 127.0.0.1:9000/WeatherStation/0 -i
