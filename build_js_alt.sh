#!/bin/bash

#!/bin/bash
# TypeScript 编译
npx tsc

# Webpack 构建
npx webpack -o tmp/alt/

# 暂停功能实现
read -p "Press any key to continue..." -n 1 -r