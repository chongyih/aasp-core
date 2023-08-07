const stringify = require("onml/stringify");

const renderControl = () => {
    const zoomIn = ['button', {id: 'zoom-in', class: 'icon-button'}, '<i class="fa fa-search-plus icon-style"></i>'];
    const zoomOut = ['button', {id: 'zoom-out', class: 'icon-button'}, '<i class="fa fa-search-minus icon-style"></i>'];
    const zoomReset = ['button', {id: 'zoom-reset', class: 'icon-button'}, '<i class="fa fa-refresh icon-style"></i>'];
    const jumpBeginning = ['button', {id: 'jump-beginning', class: 'icon-button'}, '<i class="fa fa-step-backward icon-style"></i>'];
    const shiftLeft = ['button', {id: 'shift-left', class: 'icon-button'}, '<i class="fa fa-arrow-left icon-style"></i>'];
    const shiftRight = ['button', {id: 'shift-right', class: 'icon-button'}, '<i class="fa fa-arrow-right icon-style"></i>'];
    const jumpEnd = ['button', {id: 'jump-end', class: 'icon-button'}, '<i class="fa fa-step-forward icon-style"></i>'];
    
    const controls = ['div', {class: 'controls'}, zoomIn, zoomOut, zoomReset, jumpBeginning, shiftLeft, shiftRight, jumpEnd];

    return stringify(controls)
}



module.exports = renderControl;