#!/bin/bash

set -e

SENSOR_DIR="$(pwd)/sensor_node"
SINK_DIR="$(pwd)/telemetry_sink"
CERTS_SCRIPT="$(pwd)/scripts/gen_certs.sh"

echo "--- Setting up sensor node ---"
(
    cd $SENSOR_DIR
    uv venv
    uv sync
)

echo "--- Setting up telemetry sink ---"
(
    cd $SINK_DIR
    uv venv
    uv sync
    cp .env.example .env
    
    echo "--- Creating certs --- "
    bash $CERTS_SCRIPT
)