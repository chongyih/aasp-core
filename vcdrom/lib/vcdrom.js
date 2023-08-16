'use strict';

const pkg = require('../package.json');

const createVCD = require('vcd-stream/out/vcd.js');
const webVcdParser = require('vcd-stream/lib/web-vcd-parser.js');

const stringify = require('onml/stringify.js');

const {StyleModule} = require('style-mod');

const {
  domContainer,
  pluginRenderValues,
  pluginRenderTimeGrid,
  keyBindo,
  mountTree,
  renderMenu,
  // mountCodeMirror5,
  genKeyHandler,
  genOnWheel,
  themeAll,
} = require('@wavedrom/doppler');

const {mountCodeMirror6} = require('waveql');

const getReaders = require('./get-readers.js');
const vcdPipeDeso = require('./vcd-pipe-deso.js');
const dropZone = require('./drop-zone.js');
const getWaveql = require('./get-waveql.js');
const getListing = require('./get-listing.js');
const getVcd = require('./get-vcd.js');
const getJsonls = require('./get-jsonls.js');
const getElement = require('./get-element.js');
const pluginLocalStore = require('./plugin-local-store.js');
const renderControl = require('./render-control.js');
const getControl = require('./get-control.js');
const pluginRenderTime = require('./plugin-render-time');


const getHandler = (content, inst) => async readers => {

  const waveql = await getWaveql(readers);
  const listing = await getListing(readers);
  const jsonls = await getJsonls(readers);
  const timeOpt = readers.find(row => row.key === 'time');

  vcdPipeDeso({}, inst, deso => {
    // console.log('parsed', deso);
    content.innerHTML = '';
    deso.waveql = waveql;
    deso.listing = listing;
    deso.timeOpt = timeOpt;
    deso.jsonls = jsonls;

    const elemento = mountTree.defaultElemento
    elemento['time'] = ['div', {class: 'wd-time'}]
    elemento['selectvalue'] = ['div', {class: 'wd-selectvalue'}]

    const layers = mountTree.defaultLayers.concat('time').concat('selectvalue');

    const container = domContainer({
      elemento: elemento,
      layers: layers,
      renderPlugins: [
        pluginRenderTimeGrid,
        pluginRenderValues,
        pluginLocalStore,
        pluginRenderTime,
      ]
    });

    const {render} = container.start(content, deso);

    container.elo.menu.innerHTML = renderControl();

    // ['container', 'cursor', 'view0', 'values', 'sidebar', 'menu']
    //   .map(id => ({id, el: container.elo[id]}))
    //   .concat(
    //     {id: 'document', el: document}
    //   )
    //   .map(o => {
    //     o.el.addEventListener('scroll', () => {
    //       console.log('scroll ' + o.id);
    //     });
    //   });

    const cm = mountCodeMirror6(
      container.elo.sidebar,
      deso,
      container.pstate,
      render
    );
    getControl(container.pstate, container.elo, render, cm);
    mouseClickHandler(deso, container.elo, container.pstate);

    // initial load at t = 0
    container.elo.time.style.left = (container.pstate.xOffset - 160) + 'px';

    //container.elo.container.addEventListener('keydown', genKeyHandler.genKeyHandler(content, container.pstate, render, cm, keyBindo));
    //container.elo.container.addEventListener('wheel', genOnWheel(content, container.pstate, render, cm, keyBindo));
    // console.log(cm);
  });

  await getVcd(readers, content, inst);
};

const mouseClickHandler = (deso, els, pstate) => {
  const { xOffset, xScale, tgcd } = pstate;

  const xmargin = 160;
  const handler = event => {
      const x = pstate.xTime = event.clientX;
      els.time.style.left = (x - xmargin) + 'px';
      
      updateValueCol(deso, els, event.clientX, pstate)
  };
  handler({clientX: pstate.xCursor});
  els.view0.addEventListener('click', handler);
  
  const handler2 = () => {
    updateValueCol(deso, els, pstate.xTime, pstate)
  }
  document.getElementById('shift-left').addEventListener('click', handler2);
  document.getElementById('shift-right').addEventListener('click', handler2);
  document.getElementById('zoom-in').addEventListener('click', handler2);
  document.getElementById('zoom-out').addEventListener('click', handler2);
  document.getElementById('zoom-reset').addEventListener('click', handler2);
};

const updateValueCol = (deso, els, xTime, pstate) => {
  var values = [];
  deso.view.forEach((item) => {
    const ref = item.ref;

    if (ref) {
      const xx = ((xTime - pstate.xOffset) / pstate.xScale);
      const matchingWaveValues = deso.chango[ref].wave.filter((wave) => wave[0] <= xx).at(-1);
      // check if the value is not X
      if (matchingWaveValues && !matchingWaveValues[2]) {
        values.push(['span', {class: 'wd-value'}, matchingWaveValues[1]]);
      } else {
        values.push(['span', {class: 'wd-value'}, 'X']);
      }
    } else {
      values.push(['span', {class: 'wd-value-hidden'}, 'X']);
    }
  });
  els.selectvalue.innerHTML = stringify(['div', {class: 'wd-valuecol'}].concat(values));
};


global.VCDrom = async (divName, vcdFile) => {
  console.log(pkg.name, pkg.version);
  const content = getElement(divName);

  const themeAllMod = new StyleModule(themeAll);
  StyleModule.mount(document, themeAllMod);

  //content.innerHTML = stringify(dropZone({width: 2048, height: 2048}));

  const mod = await createVCD();
  const inst = await webVcdParser(mod); // VCD parser instance
  const handler = getHandler(content, inst);
  await getReaders(handler, vcdFile);
};

/* eslint-env browser */
