#!/bin/bash

mkdir -p tmp
jq --indent 4 ".use_su = false | .use_gadget = true" conf/config.json > tmp/config.json
mv -f tmp/config.json conf/config.json