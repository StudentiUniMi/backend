#!/bin/bash
. .env
docker stack deploy -c docker-compose.yml studunimi-backend
