#!/bin/bash -e

export KAFKA_VERSION='0.10.2.0'
./build_integration.sh
tox -e pypy
