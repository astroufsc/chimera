#! /bin/bash

TESTS_DIR=`dirname $0`

export PYTHONPATH=$TESTS_DIR/../src/:$PYTHONPATH

if [[ ! `which pyflakes` ]]; then
    echo "You don't have pyflakes on the PATH."
    exit 1
fi

find $TESTS_DIR/../src/ -name '*.py' | xargs pyflakes | tee chimera.pyflakes.log
