Blockly.Blocks['1632297677993'] = {
  init: function() {
    this.jsonInit({
      "type": "1632297677993",
      "message0": "Left02move",
      "previousStatement": null,
      "nextStatement": null,
      "colour": '#C643F1',
      "toolip": "",
      "helpUrl": ""
    });
  }
};

Blockly.Lua['1632297677993'] = function(block) {
  var code = "MOTOsetspeed(30)\nMOTOrigid16(20,20,20,85,85,95,85,85,20,20,20,85,85,95,85,85,0,0,0)\nMOTOsetspeed(30)\nMOTOmove19(80, 40, 100, 94, 93, 54, 124, 90, 120, 160, 100, 106, 107, 146, 76, 100, 128, 71, 0)\nMOTOwait()\nDelayMs(100)\nMOTOsetspeed(12)\nMOTOmove19(80, 40, 100, 98, 93, 54, 123, 102, 120, 160, 100, 109, 107, 146, 76, 112, 128, 71, 0)\nMOTOwait()\nMOTOsetspeed(9)\nMOTOmove19(80, 40, 100, 98, 93, 54, 123, 102, 120, 160, 100, 103, 105, 139, 81, 109, 128, 71, 0)\nMOTOwait()\nDelayMs(100)\nMOTOsetspeed(6)\nMOTOmove19(80, 30, 100, 100, 93, 55, 124, 100, 120, 170, 100, 100, 107, 145, 76, 100, 128, 71, 0)\nMOTOwait()\n";
  return code;
}

