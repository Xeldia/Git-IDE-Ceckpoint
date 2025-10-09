#!/bin/bash
set -e
envsubst '__PORT__' < /app/nginx.conf > /etc/nginx/nginx.conf
exec nginx -g "daemon off;"