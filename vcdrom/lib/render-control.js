const stringify = require("onml/stringify");

const renderControl = () => {
    const zoomIn = ['button', {id: 'zoom-in'}, '+'];
    const zoomOut = ['button', {id: 'zoom-out'}, '-'];
    const zoomReset = ['button', {id: 'zoom-reset'}, '0'];
    const jumpBeginning = ['button', {id: 'jump-beginning'}, 'Start'];
    const jumpEnd = ['button', {id: 'jump-end'}, 'End'];
    const shiftLeft = ['button', {id: 'shift-left'}, '<'];
    const shiftRight = ['button', {id: 'shift-right'}, '>'];

    const controls = ['div', {class: 'controls'}, zoomIn, zoomOut, zoomReset, jumpBeginning, jumpEnd, shiftLeft, shiftRight];

    return stringify(controls)
}



module.exports = renderControl;