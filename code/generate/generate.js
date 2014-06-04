// Scale


var color = d3.scale.category10();




// Auxiliary Functions



function lerp (v1, v2, t) {
  return v1 * (1 - t) + v2 * t;
}



// Init Functions



function initState (state, nodes) {
  state.surface = state.width * state.height;
  state.maxPopulation = _.reduce(nodes, function (memo, node) {
    return Math.max(memo, node.population);
  }, 0);
  state.maxArea = _.reduce(nodes, function (memo, node) {
    return Math.max(memo, node.area);
  }, 0);
  resetState(state);
}



function resetState (state) {
  state.density = state.startDensity;
}



function landMass (d, state) {
  var mass = 1;
  mass += state.popScale * Math.pow(d.population / state.maxPopulation, state.sizePower);
  mass += state.areaScale * Math.pow(d.area / state.maxArea, state.sizePower);
  return mass;
}



function evenDensity (nodes, x, xLo, xHi, octaves) {
  var center = null;
  var total = 0.0;
  var mass = 0.0;

  _.each(nodes, function (node, i) {
    total += node[x] * node.mass;
    mass += node.mass;
  });

  center = total / mass;
  
  var w = (xHi - xLo) / 2;
  var scaleLeft = w / (center - xLo);
  var scaleRight = w / (xHi - center);

  var filter = function (node) {
    return node[x] < center;
  };
  var nodesLeft = _.filter(nodes, filter);
  var nodesRight = _.reject(nodes, filter);

  _.each(nodesLeft, function (node, i) {
    node[x] = xLo + (node[x] - xLo) * scaleLeft;
  });
  _.each(nodesRight, function (node, i) {
    node[x] = xLo + w + (node[x] - center) * scaleRight;
  });

  if (octaves > 0) {
    evenDensity(nodesLeft, x, xLo, xLo + w, octaves - 1);
    evenDensity(nodesRight, x, xLo + w, xHi, octaves - 1);
  }
  
}



function nodeHome (node, state) {
  return {
    "x": lerp(node.xHome, node.xHomeEven, state.homeEvenDensity),
    "y": lerp(node.yHome, node.yHomeEven, state.homeEvenDensity)
  };
}



function initLandNodes (landNodes, state) {
  var latitude = d3.scale.linear().domain([90, -90]).range([0, state.height]);
  var longitude = d3.scale.linear().domain([-180, 180]).range([0, state.width]);

  landNodes.forEach(function(d, i) {
    d.xHome = longitude(d.x);
    d.yHome = latitude(d.y);
    d.xHomeEven = d.xHome;
    d.yHomeEven = d.yHome;
    d.links = [];
  });

  updateLandNodes(landNodes, state);

  evenDensity(landNodes, "xHomeEven", 0, state.width, 4);
  evenDensity(landNodes, "yHomeEven", 0, state.height, 4);

  landNodes.forEach(function(d, i) {
    var home = nodeHome(d, state);
    d.x = home.x;
    d.y = home.y;
  });
}



function updateLandNodes (landNodes, state) {
  var totalMass = 0.0;
  landNodes.forEach(function(d, i) {
    d.mass = landMass(d, state);
    totalMass += d.mass;
  });
  var massAreaRatio = state.surface * state.density / totalMass;
  landNodes.forEach(function(d, i) {
    d.radius = Math.sqrt(d.mass * massAreaRatio / Math.PI);
  });
}



function initLandLinks (landNodes, landLinks) {
  landLinks.forEach(function(link, i) {
    link.weight = Math.max(link.perimeter / landNodes[link.source].perimeter, link.perimeter / landNodes[link.target].perimeter);
    landNodes[link.source].links.push(link.target);
    landNodes[link.target].links.push(link.source);
  });
}



// Calculate functions



function centerOfMass(nodes) {
  var xSum = 0.0;
  var ySum = 0.0;
  var sum = 0.0;
  nodes.forEach(function(d, i) {
    xSum += d.x * d.mass;
    ySum += d.y * d.mass;
    sum += d.mass;
  });

  if (sum === 0.0) {
    return [0.0, 0.0];
  }
  
  return {
    "x": xSum / sum,
    "y": ySum / sum
  };
}



function boundingBox(nodes) {
  var xLo = null;
  var xHi = null;
  var yLo = null;
  var yHi = null;
  nodes.forEach(function(d, i) {
    if (_.isNull(xLo)) {
      xLo = d.x - d.radius;
      xHi = d.x + d.radius;
      yLo = d.y - d.radius;
      yHi = d.y + d.radius;
    } else {
      xLo = Math.min(xLo, d.x - d.radius);
      xHi = Math.max(xHi, d.x + d.radius);
      yLo = Math.min(yLo, d.y - d.radius);
      yHi = Math.max(yHi, d.y + d.radius);
    }
  });

  return {
    "xLo": xLo,
    "xHi": xHi,
    "yLo": yLo,
    "yHi": yHi
  };
}



// D3



function createNodes (svg, nodes) {
 var d3Node = svg.selectAll(".node")
    .data(nodes)
    .enter().append("g")
    .attr("class", "node");

  d3Node.append("circle");

  d3Node.append("text")
    .attr("dy", ".35em")
    .attr("text-anchor", "middle")
    .text(function(d) { return d.code; });

  d3Node.append("title")
    .text(function(d) { return d.name; });

  return d3Node;
}



function createLinks(svg, links) {
  var d3Link = svg.selectAll(".link")
    .data(links)
    .enter().append("line")
    .attr("class", "link")
    .style("stroke", function (d) { return color("line"); })
  return d3Link;
}



function draw (svg, node, link, options) {
  if (options.drawLinks) {
    link
      .attr("x1", function(d) {return d.source.x;})
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; })
      .style("stroke-width", function(d) { return Math.min(d.source.radius, d.target.radius) * d.weight; })
      .style("stroke", function(d) { return color(d.source.continent); })
  }

  if (options.drawNodes) {
    node
      .attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")";
      });

    node.selectAll("circle")
      .attr("r", function(d) { return d.radius })
      .style("fill", function(d) {return color(1) })
    node.selectAll("text")
      .style("font-size", function(d) { return d.radius; })
  }

}



// Node Functions



function nodeCollide(node, state) {
  var r = node.radius + 16,
  nx1 = node.x - r,
  nx2 = node.x + r,
  ny1 = node.y - r,
  ny2 = node.y + r;
  return function(quad, x1, y1, x2, y2) {
    if (quad.point && (quad.point !== node)) {
      var x = node.x - quad.point.x;
      var y = node.y - quad.point.y;
      var l = Math.sqrt(x * x + y * y);
      var r = node.radius + quad.point.radius;
      if (_.indexOf(node.links, quad.point.index) == -1) {
        // Nodes are not land linked
        r += state.seaDistance;
        if (node.group != quad.point.group) {
          r += state.groupDistance;
        }
      }
      if (l < r) {
        l = (l - r) / l * .5;
        node.x -= x *= l;
        node.y -= y *= l;
        quad.point.x += x;
        quad.point.y += y;
      }
    }
    return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
  }
}



function nodeHomeTether(alpha, state) {
  return function(d) {
    var home = nodeHome(d, state);
    d.x += (home.x - d.x) * alpha * d.mass;
    d.y += (home.y - d.y) * alpha * d.mass;
  };
}



function nodeFrame(alpha, com, bbox, state) {
  var xScale = (state.width - 2 * state.framePadding) / (bbox.xHi - bbox.xLo);
  var yScale = (state.height - 2 * state.framePadding) / (bbox.yHi - bbox.yLo);

  return function(d) {
    var dx = (d.x - bbox.xLo) * xScale + state.framePadding - d.x;
    var dy = (d.y - bbox.yLo) * yScale + state.framePadding - d.y;
    d.x += dx * alpha;
    d.y += dy * alpha;
  };
}



// Force


function initForce (force, nodes, links, state, startCallback, tickCallback, endCallback) {
  force
    .size([state.width, state.height])
    .nodes(nodes)
    .links(links)
    .gravity(0);

  if (!_.isNull(state.chargeGain)) {
    force.charge(function (d) {
      return state.chargeGain;
    });
  }

  if (!_.isNull(state.linkGain)) {
    force
      .linkDistance(function(d) { 
        return d.source.radius + d.target.radius;
      })
      .linkStrength(function(d) {
        return d.weight * Math.min(state.linkGain, state.ticks * 0.1);
      });
  }

  force.on("start", function(e) {
    console.log("Force start");
    startCallback(e);
  });

  force.on("end", function(e) {
    if (force.dragging) {
      return;
    }
    console.log("Force end");
    endCallback(e);
  });

  force.on("tick", tickCallback);
}



function forceTick (e, d3Node, nodes, state, callback) {
  var landQuad = d3.geom.quadtree(nodes);

  state.ticks += 1;

  if (state.density > state.targetDensity) {
    state.density -= state.stepDensity;
    updateLandNodes(nodes, state);
  }
  if (state.density < state.targetDensity) {
    state.density += state.stepDensity;
    updateLandNodes(nodes, state);
  }

  i = 0;
  n = nodes.length;
  while (++i < n) {
    landQuad.visit(nodeCollide(nodes[i], state)); 
  }

  if (state.homeGain) {
    d3Node.each(nodeHomeTether(state.homeGain * e.alpha, state));
  }

  if (state.frameGain) {
    var com = centerOfMass(nodes);
    var bbox = boundingBox(nodes);
    d3Node.each(nodeFrame(state.frameGain * e.alpha, com, bbox, state));
  }

  callback();
}



// Form

function initSlider (name, decimalPlaces, state, update) {
  var $slider = $("input[name='" + name + "']");
  function value () {
    return parseFloat($slider.val());
  }
  
  function updateValue () {
    $slider.parent().children("span.value").text(value().toFixed(decimalPlaces));
  }

  $slider.mouseup(function (e) {
    state[name] = value();
    updateValue();
    update();
  });

  $slider.mousemove(function (e) {
    if (e.which != 1) {
      return;
    }
    updateValue();
  });

  $slider.val(state[name]);
  updateValue();
}



function getButtons () {
  return {
    "$stop": $("button[name='stop']"),
    "$resume": $("button[name='resume']"),
    "$reset": $("button[name='reset']"),
    "$save": $("button[name='save']")
  };
}



function initForm (stop, resume, reset, save, state, update) {
  var $form = $("form");
  var buttons = getButtons();

  $form.width(state.width);

  buttons.$stop.click(function (e) {
    e.preventDefault();
    stop()
  });
  buttons.$resume.click(function (e) {
    e.preventDefault();
    resume()
  });
  buttons.$reset.click(function (e) {
    e.preventDefault();
    reset()
  });
  buttons.$save.click(function (e) {
    e.preventDefault();
    save()
  });

  initSlider("targetDensity", 3, state, update);
  initSlider("sizePower", 3, state, update);
  initSlider("popScale", 1, state, update);
  initSlider("areaScale", 1, state, update);
  initSlider("chargeGain", 1, state, update);
  initSlider("linkGain", 1, state, update);
  initSlider("homeGain", 2, state, update);
  initSlider("homeEvenDensity", 2, state, update);
  initSlider("frameGain", 2, state, update);
  initSlider("framePadding", 0, state, update);
  initSlider("seaDistance", 0, state, update);
  initSlider("groupDistance", 0, state, update);
}



// Main



d3.json("dots.json", function (error, graph) {
  var state = {
    "width": 800,
    "height": 450,

    "popScale": 5,
    "areaScale": 2.5,
    "sizePower": 0.5,

    "startDensity": 0.05,
    "targetDensity": 0.4,
    "stepDensity": 0.002,

    "chargeGain": 0,  // Default -30. Positive": attract, negative": repel.
    "linkGain": 38.0,  // Default 1
    "homeGain": 0.8,
    "homeEvenDensity": 1.0,
    "frameGain": 3.0,
    "framePadding": 30.0,

    "seaDistance": 5.0,
    "groupDistance": 22.0,

    "surface": null,
    "maxPopulation": null,
    "maxArea": null,
    "ticks": null,
    "alpha": null,
    "density": null
  }

  var options = {
    "drawNodes": true,
    "drawLinks": false,

    "restartAlpha": 0.03
  }

  var svg = d3.select("#dotmap").append("svg")
    .attr("width", state.width)
    .attr("height", state.height);

  initState(state, graph.nodes);
  initLandNodes(graph.nodes, state);
  initLandLinks(graph.nodes, graph.links);
  
  var d3Node = createNodes(svg, graph.nodes);
  var d3Link = createLinks(svg, graph.links);

  var force = d3.layout.force();

  var buttons = getButtons();
  var $alphaInput = $("input[name='alpha']");
  var $alphaValue = $alphaInput.parent().children("span.value");
  var $densityInput = $("input[name='density']");
  var $densityValue = $densityInput.parent().children("span.value");

  var updateValues = function (state) {
    if (!_.isNull(state.alpha)) {
      $alphaInput.val(state.alpha);
      $alphaValue.text(state.alpha.toFixed(3));
    }
    if (!_.isNull(state.density)) {
      $densityInput.val(state.density);
      $densityValue.text(state.density.toFixed(3));
    }
  }

  var forceStartCallback = function (e) {
    buttons.$stop.prop("disabled", false);
    buttons.$resume.prop("disabled", true);
    force.stopAlpha = undefined;
  };

  var forceTickCallback = function (e) {
    forceTick(e, d3Node, graph.nodes, state, function () {
      state.alpha = parseFloat(force.alpha());
      draw(svg, d3Node, d3Link, options);
      updateValues(state);
    });
    force.update();
  };

  var forceEndCallback = function (e) {
    state.alpha = parseFloat(force.alpha());
    buttons.$stop.prop("disabled", true);
    buttons.$resume.prop("disabled", false);
    updateValues(state);
  };

  var buttonStopCallback = function () {
    force.stopAlpha = force.alpha();
    force.stop();
  };

  var buttonResumeCallback = function () {
    if (!!force.stopAlpha) {
      force.alpha(force.stopAlpha);
    } else {
      force.alpha(0.03);
    }
  };

  var buttonResetCallback = function () {
    force.stop();
    state.density = state.startDensity;
    updateLandNodes(graph.nodes, state);
    graph.nodes.forEach(function(d, i) {
      d.px = d.x;
      d.py = d.y;
    });
    state.ticks = 0;
    force.start();
  };

  var buttonSaveCallback = function () {
    data = {
      "state": state,
      "nodes": []
    };

    graph.nodes.forEach(function(d, i) {
      data.nodes.push({
        "code": d.code,
        "name": d.name,
        "radius": d.radius,
        "x": d.x,
        "y": d.y
      })
    });

    $.ajax({
      type: "POST",
      url: "/save",
      data: JSON.stringify(data),
      success: function (data, textStatus, jqXHR) {
        console.log("Saved: ", data.path);
      }
    });
  };

  var formUpdateCallback = function () {
    force.update();
    if (force.alpha() < options.restartAlpha) {
      force.alpha(options.restartAlpha);
    }
  };

  initForce(force, graph.nodes, graph.links, state,
            forceStartCallback, forceTickCallback, forceEndCallback);
  initForm(buttonStopCallback, buttonResumeCallback, buttonResetCallback, 
           buttonSaveCallback, state, formUpdateCallback);

  draw(svg, d3Node, d3Link, options);

  force.ticks = 0;
  force.start();

  console.log("End.");
});
