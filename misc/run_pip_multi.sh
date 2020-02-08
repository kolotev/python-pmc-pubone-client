#!/bin/bash

source $(dirname $0)/.init.rc

set -x
# --no-upgrade
pip-compile-multi --use-cache "$@"

