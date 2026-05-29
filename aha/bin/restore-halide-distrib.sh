#!/bin/bash

# What does this script do?

# To save space (400M!), Dockerfile deletes halide bin and lib
# "distrib" files before building the final docker image.
# This script restores them from a compressed tar file
# that conveniently already exists(!)

# This script is designed to be run as the docker image's "ENTRYPOINT",
# so that it will run exactly *once*, at initial container launch.

: "${AHA_HOME:=/aha-agate}"

echo "--- Restore ${AHA_HOME}/Halide-to-Hardware/distrib/{bin,lib}"
(
    cd ${AHA_HOME}/Halide-to-Hardware/distrib
    tar xvf halide.tgz halide/bin; mv halide/bin bin
    tar xvf halide.tgz halide/lib; mv halide/lib lib
)
echo "halide/distrib restored:"
ls -lh ${AHA_HOME}/Halide-to-Hardware/distrib/{bin,lib}/*
echo ""

# When this script runs as a Dockerfile ENTRYPOINT, this next line
# runs whatever commands get passed via e.g. "docker run"
exec "$@"
