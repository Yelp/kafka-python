#!/bin/bash -e

export KAFKA_VERSION='0.10.2.2'
./build_integration.sh
tox -e pypy
