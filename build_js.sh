#!/bin/bash

mkdir -p tmp
npx frida-compile -S src/script/native/index.ts -o tmp/native.js
npx frida-compile -S src/script/java/index.ts -o tmp/java.js
npx frida-compile -S src/script/extra/index.ts -o tmp/extra.js
npx frida-compile -S src/script/trainer/index.ts -o tmp/trainer.js