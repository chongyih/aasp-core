'use strict';

const genSVG = require("onml/gen-svg");
const stringify = require("onml/stringify");

const pluginRenderTime = (desc, pstate, els) => {
    const xmargin = 160;
    const fontHeight = 20;
    const fontWidth = fontHeight / 2;
    const {height, xScale, xOffset, tgcd, timescale, xCursor} = pstate;

    const body = [
        // vertical line
        ['line', {
          class: 'wd-cursor-line',
          x1: xmargin + 0.5,
          x2: xmargin + 0.5,
          y1: 0,
          y2: height
        }],
      ];
    
    els.time.innerHTML = stringify(genSVG(2 * xmargin, height).concat(body));
}

module.exports = pluginRenderTime;
