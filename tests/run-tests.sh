#! /bin/bash

TESTS_DIR=`dirname $0`

export PYTHONPATH=$TESTS_DIR/../src/:$PYTHONPATH

if [[ ! `which nosetests` ]]; then
    echo "You don't have nosetests on the PATH."
    exit 1
fi

nosetests --with-coverage --cover-erase --cover-package=chimera $TESTS_DIR/../src/chimera -v $@ | tee $TESTS_DIR/tests.log
