#! /bin/bash

DOCS_DIR=`dirname $0`

export PYTHONPATH=$DOCS_DIR/../src/:$PYTHONPATH

if [[ ! `which epydoc` ]]; then
    echo "You don't have epydoc on the PATH."
    exit 1
fi

epydoc --pdf -o doc.pdf --config=$DOCS_DIR/chimera.epydoc -v $@
