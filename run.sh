#!/bin/bash
set -e
trap 'trap - SIGTERM && kill -- -$$' SIGINT SIGTERM EXIT

export SERIAL_SERVER_PORT=$(./get_free_port.sh)
PYTHONUNBUFFERED=1 python simulator/serial_server.py &
python3 -c "import time; time.sleep(0.1)"

export MICROPYPATH="$(pwd)/simulator"
micropython firmware/main.py
