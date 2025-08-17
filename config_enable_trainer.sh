#!/bin/bash

mkdir -p tmp
jq --indent 4 ".enable_trainer = true" conf/config.json > tmp/config.json
mv -f tmp/config.json conf/config.json