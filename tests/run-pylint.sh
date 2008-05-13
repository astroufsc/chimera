#! /bin/bash

TESTS_DIR=`dirname $0`

export PYTHONPATH=$TESTS_DIR/../src/:$PYTHONPATH

if [[ ! `which pylint` ]]; then
    echo "You don't have pylint on the PATH."
    exit 1
fi

pylint --rcfile=$TESTS_DIR/chimera.pylint $@ chimera >| $TESTS_DIR/chimera.pylint.html
