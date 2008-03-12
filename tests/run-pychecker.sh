#! /bin/bash

TESTS_DIR=`dirname $0`

export PYTHONPATH=$TESTS_DIR/../src/:$PYTHONPATH

if [[ ! `which pychecker` ]]; then
    echo "You don't have pychecker on the PATH."
    exit 1
fi

find $TESTS_DIR/../src/chimera/ -name '*.py' | xargs pychecker -F $TESTS_DIR/chimera.pychecker | tee chimera.pychecker.log
