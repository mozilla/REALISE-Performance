// Based on: //https://github.com/benalexkeen/d3-flask-blog-post/blob/master/templates/index.html
// And: https://bl.ocks.org/mbostock/35964711079355050ff1
function preprocessData(data) {
	var n = 0;
	cleanData = [];
	run = [];
	for (i=0; i<data.values[0].raw.length; i++) {
		d = data.values[0].raw[i];
		if (isNaN(d)) {
			n++; // keep counting!
			if (run.length > 0)
				cleanData.push(run);
			run = [];
			continue;
		}
		// NOTE: remember that this *must* be 0-based indexing, as the 
		// change point index is ultimately retrieved from this X 
		// value and the Python code is 0-based as well. Thus, the 
		// first item should get X = 0.
		run.push({"X": n++, "Y": d});
	}
	cleanData.push(run);
	return cleanData;
} 

function scaleAndAxis(data, width, height) {
	// xScale is the active scale used for zooming, xScaleOrig is used as 
	// the original scale that is never changed.
	var xScale = d3.scaleLinear().range([0, width]);
	var xScaleOrig = d3.scaleLinear().range([0, width]);
	var yScale = d3.scaleLinear().range([height, 0]);
	var yScaleOrig = d3.scaleLinear().range([height, 0]); // Define yScaleOrig here


	// create the axes
	var xAxis = d3.axisBottom(xScale);
	var yAxis = d3.axisLeft(yScale);

	// turn off ticks on the y axis. We don't want annotators to be 
	// influenced by whether a change is big in the absolute sense.
	yAxis.ticks(10);

	var xmin = Math.min(...data.map(function(run) { return Math.min(...run.map(it => it.X)); }))
	var xmax = Math.max(...data.map(function(run) { return Math.max(...run.map(it => it.X)); }))
	var ymin = Math.min(...data.map(function(run) { return Math.min(...run.map(it => it.Y)); }))
	var ymax = Math.max(...data.map(function(run) { return Math.max(...run.map(it => it.Y)); }))
	var xExtent = [xmin, xmax];
	var yExtent = [ymin, ymax];

	// compute the domains for the axes
	//var xExtent = d3.extent(data, function(d) { return d.X; });
	var xRange = xExtent[1] - xExtent[0];
	var xDomainMin = xExtent[0] - xRange * 0.02;
	var xDomainMax = xExtent[1] + xRange * 0.02;

	//var yExtent = d3.extent(data, function(d) { return d.Y; });
	var yRange = yExtent[1] - yExtent[0];
	var yDomainMin = yExtent[0] - yRange * 0.05;
	var yDomainMax = yExtent[1] + yRange * 0.05;

	// set the axis domains
	xScale.domain([xDomainMin, xDomainMax]);
	xScaleOrig.domain([xDomainMin, xDomainMax]);
	yScale.domain([yDomainMin, yDomainMax]);
	yScaleOrig.domain([yDomainMin, yDomainMax]);

	return [xAxis, yAxis, xScale, xScaleOrig, yScale, yScaleOrig, yDomainMin, yDomainMax];
}



function noZoom() {
	d3.event.preventDefault();
}

function baseChart(
	selector,
	data,
	clickFunction,
	annotations,
	annotationFunction,
	divWidth,
	divHeight
) {
	if (divWidth === null || typeof divWidth === 'undefined')
		divWidth = 1200;
	if (divHeight === null || typeof divHeight === 'undefined')
		divHeight = 480;

	// preprocess the data
	data = preprocessData(data);

	var svg = d3.select(selector)
		.on("touchstart", noZoom)
		.on("touchmove", noZoom)
		.append("svg")
		.attr("width", divWidth)
		.attr("height", divHeight)
		.attr("viewBox", "-25 0 " + divWidth + " " + divHeight);

	var margin = {top: 20, right: 20, bottom: 50, left: 50};
	var width = +svg.attr("width") - margin.left - margin.right;
	var height = +svg.attr("height") - margin.top - margin.bottom;

	var [xAxis, yAxis, xScale, xScaleOrig, yScale, yScaleOrig, yDomainMin, yDomainMax] = scaleAndAxis(
		data,
		width,
		height);

	var lineObjects = [];
	for (let r=0; r<data.length; r++) {
		var lineObj = new d3.line()
			.x(function(d) { return xScale(d.X); })
			.y(function(d) { return yScale(d.Y); });
		lineObjects.push(lineObj);
	}

	var zoomX = d3.zoom()
    .scaleExtent([1, 100])
    .translateExtent([[0, 0], [width, height]])
    .extent([[0, 0], [width, height]])
	.wheelDelta(() => -d3.event.deltaY * 0.002)
    .on("zoom", zoomTransformX);

	var zoomY = d3.zoom()
		.scaleExtent([1, 100])
		.translateExtent([[0, 0], [width, height]])
		.extent([[0, 0], [width, height]])
		.wheelDelta(() => -d3.event.deltaY * 0.004)
		.on("zoom", zoomTransformY);

	var currentZoom = zoomX; // Default: X-axis zooming



	function zoomTransformX() {
		const transform = d3.event.transform;
		const mouseX = d3.mouse(svg.node())[0]; // Get mouse X position relative to the SVG
		const mouseDomainX = xScale.invert(mouseX); // Convert mouse X to domain value
	
		// Transform only the x-axis
		xScale.domain(transform.rescaleX(xScaleOrig).domain());
	 
		// Adjust the domain to center around the mouse position
		const newMouseDomainX = xScale.invert(mouseX);
		const domainShift = mouseDomainX - newMouseDomainX;
		xScale.domain(xScale.domain().map(d => d + domainShift));
	
		for (let r = 0; r < data.length; r++) {
			svg.select(".line-" + r).attr("d", lineObjects[r]);
	
			// Transform the circles
			pointSets[r].data(data[r])
				.attr("cx", d => xScale(d.X))
				.attr("cy", d => yScale(d.Y));
		}
	
		// Transform annotation lines (if any)
		annoLines = gView.selectAll("line");
		annoLines._groups[0].forEach(l => {
			l.setAttribute("x1", xScale(l.getAttribute("cp_idx")));
			l.setAttribute("x2", xScale(l.getAttribute("cp_idx")));
		});
	
		svg.select(".axis--x").call(xAxis);
	}
	
	function zoomTransformY() {
		const transform = d3.event.transform;
		const mouseY = d3.mouse(svg.node())[1]; // Get mouse Y position relative to the SVG
		const mouseDomainY = yScale.invert(mouseY); // Convert mouse Y to domain value
	
		// Rescale the Y axis using yScaleOrig
		yScale.domain(transform.rescaleY(yScaleOrig).domain());
	
		// Adjust the domain to center around the mouse position
		const newMouseDomainY = yScale.invert(mouseY);
		const domainShift = mouseDomainY - newMouseDomainY;
		yScale.domain(yScale.domain().map(d => d + domainShift));
	
		for (let r = 0; r < data.length; r++) {
			svg.select(".line-" + r).attr("d", lineObjects[r]);
	
			// Transform the circles
			pointSets[r].data(data[r])
				.attr("cx", d => xScale(d.X))
				.attr("cy", d => yScale(d.Y));
		}
	
		// Transform the annotation lines (if any)
		annoLines = gView.selectAll("line");
		annoLines._groups[0].forEach(function(l) {
			l.setAttribute("y1", yScale(l.getAttribute("cp_idx")));
			l.setAttribute("y2", yScale(l.getAttribute("cp_idx")));
		});
	
		// Update Y axis
		svg.select(".axis--y").call(yAxis);
	}


	var drag = d3.drag()
	.on("drag", function () {
		var dx = d3.event.dx * (xScale.domain()[1] - xScale.domain()[0]) / width;
		var dy = d3.event.dy * (yScale.domain()[1] - yScale.domain()[0]) / height;

		// Clamp X axis to original scale range
		const xMin = xScaleOrig.domain()[0];
		const xMax = xScaleOrig.domain()[1];
		let newX0 = xScale.domain()[0] - dx;
		let newX1 = xScale.domain()[1] - dx;

		if (newX0 < xMin) {
			newX0 = xMin;
			newX1 = newX0 + (xScale.domain()[1] - xScale.domain()[0]);
		}
		if (newX1 > xMax) {
			newX1 = xMax;
			newX0 = newX1 - (xScale.domain()[1] - xScale.domain()[0]);
		}
		xScale.domain([newX0, newX1]);

		// Optionally do the same for yScale if needed
		yScale.domain([yScale.domain()[0] + dy, yScale.domain()[1] + dy]);

		// Update axes and visuals
		svg.select(".axis--x").call(xAxis);
		svg.select(".axis--y").call(yAxis);

		for (let r = 0; r < data.length; r++) {
			svg.select(".line-" + r).attr("d", lineObjects[r]);
			pointSets[r].data(data[r])
				.attr("cx", d => xScale(d.X))
				.attr("cy", d => yScale(d.Y));
		}

		// Update annotation lines
		annoLines = gView.selectAll("line");
		annoLines._groups[0].forEach(function (l) {
			l.setAttribute("x1", xScale(l.getAttribute("cp_idx")));
			l.setAttribute("x2", xScale(l.getAttribute("cp_idx")));
			l.setAttribute("y1", yScale(l.getAttribute("cp_idx")));
			l.setAttribute("y2", yScale(l.getAttribute("cp_idx")));
		});
	});


	var zero = xScale(0);

	// clip path
	svg.append("defs")
		.append("clipPath")
		.attr("id", "clip")
		.append("rect")
		.attr("width", width - 18)
		.attr("height", height)
		.attr("transform", "translate(" + zero + ",0)");

	// y axis
	svg.append("g")
		.attr("class", "axis axis--y")
		.attr("transform", "translate(" + zero + ",0)") // Use margin.left instead of zero
		.call(yAxis);

		// x axis
	svg.append("g")
		.attr("class", "axis axis--x")
		.attr("transform", "translate(0, " + height + ")")
		.call(xAxis);

	// x axis label
	svg.append("text")
		.attr("text-anchor", "middle")
		.attr("class", "axis-label")
		.attr("transform", "translate(" + (width - 20) + "," + (height + 50) + ")")
		.text("Time");

	// wrapper for zoom
	var gZoom = svg.append("g")
	.call(currentZoom)
	.call(drag);

	gZoom.call(currentZoom);


	// Add event listener for zoom toggle
	// document.getElementById("zoomToggle").addEventListener("change", function() {
	// 	if (this.checked) {
	// 	  // Y-axis zoom
	// 	  currentZoom = zoomY;
	// 	  document.getElementById("zoomLabel").innerText = "Change zoom mode (current mode is Y-Axis Zoom)";
	// 	} else {
	// 	  // X-axis zoom
	// 	  currentZoom = zoomX;
	// 	  document.getElementById("zoomLabel").innerText = "Change zoom mode (current mode is X-Axis Zoom)";
	// 	}
	  
	// 	// Apply the current zoom behavior
	// 	gZoom.call(currentZoom);
	//   });	  



	const zoomToggle = document.getElementById("zoomToggle");

	if (zoomToggle) {
	zoomToggle.addEventListener("change", function () {
		if (this.checked) {
		currentZoom = zoomY;
		document.getElementById("zoomLabel").innerText =
			"Change zoom mode (current mode is Y-Axis Zoom)";
		} else {
		currentZoom = zoomX;
		document.getElementById("zoomLabel").innerText =
			"Change zoom mode (current mode is X-Axis Zoom)";
		}
		gZoom.call(currentZoom);
	});
	} else {
	console.warn('zoomToggle element not found, skipping event listener.');
	}

	// rectangle for the graph area
	gZoom.append("rect")
		.attr("width", width)
		.attr("height", height);

	// view for the graph
	var gView = gZoom.append("g")
		.attr("class", "view");

	// add the line(s) to the view
	for (let r=0; r<data.length; r++) {
		gView.append("path")
			.datum(data[r])
			.attr("class", "line line-"+r)
			.attr("d", lineObjects[r]);
	}

	// Render data points and save them for later zoom resets
	var pointSets = [];

	for (let r = 0; r < data.length; r++) {
		const wrap = gView.append("g");

		// Append the circles
		wrap.selectAll("circle")
			.data(data[r])
			.enter()
			.append("circle")
			.attr("cx", d => xScale(d.X))
			.attr("cy", d => yScale(d.Y))
			.attr("data_X", d => d.X)
			.attr("data_Y", d => d.Y)
			.attr("r", 5)
			.on("click", function (d, i) {
				d.element = this;
				return clickFunction(d, i);
			});

		// Select all circles *after* enter+append
		const points = wrap.selectAll("circle");

		pointSets.push(points);
	}



	// handle the annotations
	annotations.forEach(function(a) {
		for (let i = 0; i < pointSets.length; i++) {
			const group = pointSets[i];
			if (!group || !group._groups || group._groups.length === 0) continue;
			const circles = group._groups[0];
			for (let j = 0; j < circles.length; j++) {
				const p = circles[j];
				if (p.getAttribute("data_X") != a.index) continue;
				const elem = d3.select(p);
				annotationFunction(a, elem, gView, xScale, yScale, yDomainMin, yDomainMax);
			}
		}
	});
	


		// Store global context for zoom reset
		window._chartContext = {
			xScale, xScaleOrig,
			yScale, yScaleOrig,
			xAxis, yAxis,
			svg, lineObjects, data, pointSets, gView
		};
}

const changeTypes = [
	['mean', 'red', 'M'],
	['variance', 'orange', 'V'],
	['mean_variance', 'yellow', 'B'],
	['', null],
];
function annotateChart(selector, data) {
	function handleClick(d, i) {
		if (d3.event.defaultPrevented) return; // zoomed
		var elem = d3.select(d.element);
		var next = 0;
		for (var i = 0; i < changeTypes.length - 1; i++) {
			if (elem.node().classList.contains(changeTypes[i][0])) {
				next = i + 1;
			}
		}
		console.log(changeTypes[next]);
		elem.attr('stroke', 'blue');
		elem.style("fill", changeTypes[next][1]);
		elem.attr('class', changeTypes[next][0]);
		/*
		var g = elem.select(function() { return this.parentNode; });
		g.append('text')
			.attr('x', elem.attr('cx'))
			.attr('y', elem.attr('cy'))
			.text(changeTypes[next][2]);
		*/
		/*
		if (elem.classed("changepoint")) {
			elem.style("fill", null);
			elem.classed("changepoint", false);
		} else {
			elem.style("fill", "red");
			elem.classed("changepoint", true);
		}
		*/
		updateTable();
	}
	baseChart(selector, data, handleClick, [], null);
}

function viewAnnotations(selector, data, annotations) {
	function handleAnnotation(ann, elem, view, xScale, yScale, yDomainMin, yDomainMax) {
		elem.classed("marked", true);
		view.append("line")
			.attr("cp_idx", ann.index)
			.attr("y1", yScale(yDomainMax))
			.attr("y2", yScale(yDomainMin))
			.attr("x1", xScale(ann.index))
			.attr("x2", xScale(ann.index))
			.attr("class", "ann-line");
	}
	baseChart(selector, data, function() {}, annotations, handleAnnotation, null, 300);
}

function adminViewAnnotations(selector, data, annotations) {
	function handleAnnotation(ann, elem, view, xScale, yScale, yDomainMin, yDomainMax) {
		elem.classed(ann.user, true);
		view.append("line")
			.attr("cp_idx", ann.index)
			.attr("y1", yScale(yDomainMax))
			.attr("y2", yScale(yDomainMin))
			.attr("x1", xScale(ann.index))
			.attr("x2", xScale(ann.index))
			.attr("class", "ann-line" + " " + ann.user);
	}
	baseChart(selector, data, function() {}, annotations, handleAnnotation);
}

function resetZoom() {
    if (!window._chartContext) {
        console.warn("No chart context found for zoom reset");
        return;
    }

    const {
        xScale, xScaleOrig, yScale, yScaleOrig,
        xAxis, yAxis,
        svg, lineObjects, data, pointSets, gView
    } = window._chartContext;

    // Debug: print pointSets structure
    console.log("resetZoom: pointSets =", pointSets);

    // Reset scales
    xScale.domain(xScaleOrig.domain());
    yScale.domain(yScaleOrig.domain());

    // Redraw axes
    svg.select(".axis--x").call(xAxis);
    svg.select(".axis--y").call(yAxis);

    // Redraw lines and points
    for (let r = 0; r < data.length; r++) {
        svg.select(".line-" + r).attr("d", lineObjects[r]);

        if (!pointSets || !pointSets[r]) {
            console.warn(`resetZoom: pointSets[${r}] is undefined`);
            continue;
        }

        const pointGroup = pointSets[r];
        if (!Array.isArray(pointGroup._groups) || pointGroup._groups.length === 0) {
            console.warn(`resetZoom: pointSets[${r}] has invalid _groups`);
            continue;
        }

        pointGroup
            .data(data[r])
            .attr("cx", d => xScale(d.X))
            .attr("cy", d => yScale(d.Y));
    }

    // Reset annotation lines
    const annoLines = gView.selectAll("line");
    annoLines._groups[0].forEach(function (l) {
        l.setAttribute("x1", xScale(l.getAttribute("cp_idx")));
        l.setAttribute("x2", xScale(l.getAttribute("cp_idx")));
        l.setAttribute("y1", yScale(l.getAttribute("cp_idx")));
        l.setAttribute("y2", yScale(l.getAttribute("cp_idx")));
    });
}
