#!/bin/bash

docker compose down --volumes
rm -rf data logs
deactivate || true
rm -rf env