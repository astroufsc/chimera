#!/bin/bash
set -xe
chimera-filter -vvvvv --version
chimera-filter -vvvvv -h
chimera-filter -vvvvv -F
chimera-filter -vvvvv --info
chimera-filter -vvvvv -f U
chimera-filter -vvvvv -f B
chimera-filter -vvvvv --get-filter
