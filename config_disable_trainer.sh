#!/bin/bash

mkdir -p tmp
jq --indent 4 ".enable_trainer = false" conf/config.json > tmp/config.json
mv -f tmp/config.json conf/config.json