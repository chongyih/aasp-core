#!/usr/bin/bash

mkdir -p ../static/vcdrom

cp node_modules/vcd-stream/out/vcd.wasm ../static/vcdrom
cp src/*.css ../static/vcdrom
cp src/*.woff2 ../static/vcdrom

mkdir -p ../templates/vcdrom

cp src/vcdrom.html ../templates/vcdrom/vcdrom.html

./node_modules/.bin/browserify ./lib/vcdrom.js | ./node_modules/.bin/terser --compress -o ../static/vcdrom/vcdrom.js
