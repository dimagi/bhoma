#!/bin/bash

lsof -n | gzip -c > /tmp/lsof.$(date +%Y%m%d%H%M%S).gz
