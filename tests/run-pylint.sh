#! /bin/bash

TESTS_DIR=`dirname $0`

export PYTHONPATH=$TESTS_DIR/../src/:$TESTS_DIR/../../Pyro-3.7/

pylint --rcfile=$TESTS_DIR/chimera.pylint chimera >| $TESTS_DIR/pylint.html
