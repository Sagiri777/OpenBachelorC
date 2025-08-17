#!/bin/bash

mkdir -p tmp
jq --indent 4 ".use_su = true | .use_gadget = false" conf/config.json > tmp/config.json
mv -f tmp/config.json conf/config.json