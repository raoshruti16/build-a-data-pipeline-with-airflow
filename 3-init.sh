#!/bin/bash

mkdir -p ./data ./logs

docker-compose run --rm webserver airflow db init
docker-compose run --rm webserver airflow users create \
    --username admin \
    --firstname admin \
    --lastname admin \
    --role Admin \
    --password admin \
    --email admin@example.com

docker-compose up --build -d