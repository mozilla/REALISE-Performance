function resetOnClick() {
	var changepoints = getChangepoints();
	for (const cp of changepoints) {
		var elem = d3.select(cp);
		elem.style("fill", "blue");
                elem.attr('class', '');
	}
	updateTable();
	location.reload();
}

// function resetOnClick() {
//     var changepoints = getChangepoints();
//     for (const cp of changepoints) {
//         var elem = d3.select(cp);
//         elem.style("fill", "blue");
//         elem.attr('class', '');
//     }
//     updateTable();
    
//     // Reset zoom transform
//     var svg = d3.select("svg"); // Ensure this targets your main SVG
//     svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
// }


function validateDifficulty() {
	var difficulty = document.querySelector('input[name="difficulty"]:checked');
	if (difficulty === null) {
		$('#NoDifficultyModal').modal();
		return false;
	}
    return true;
}

function askForProblem(subFun, identifier, startTime) {
    $("#ReportProblemModal").on("hidden.bs.modal", function () {
        document.getElementById("problem-text").value = "";
    });
    document.getElementById("btn-modal-report").onclick = function() {
       subFun(identifier, startTime); 
    }
	var problem = document.querySelector('input[name="problem"]:checked');
    var problemText = document.getElementById("problem-text").value;
    if (problem !== null && problemText === "") {
		$('#ReportProblemModal').modal();
        return false;
    }
    return true;
}

function noCPOnClick(identifier, startTime) {
	var changepoints = getChangepoints();
	if (changepoints.length > 0) {
		$('#NoCPYesCPModal').modal();
		return false;
	}

    if (!validateDifficulty()) {
        return;
    }

    if (!askForProblem(noCPOnClick, identifier, startTime)) {
        return;
    }

	var difficulty = document.querySelector('input[name="difficulty"]:checked');

	var obj = {}
	obj["identifier"] = identifier;
	obj["difficulty"] = difficulty.value;
	obj["changepoints"] = null;
	obj["time_spent"] = new Date() - startTime;
    obj["problem"] = document.getElementById('problem-text').value;

	var xhr = new XMLHttpRequest();
	xhr.open("POST", "", false);
	xhr.withCredentials = true;
	xhr.setRequestHeader("Content-Type", "application/json");
	/* Flask's return to this POST must be a URL, not a template!*/
	xhr.onreadystatechange = function() {
		if (xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
			window.location.href = xhr.responseText;
			console.log("XHR Success: " + xhr.responseText);
		} else {
			console.log("XHR Error: " + xhr.status);
		}
	}
	xhr.send(JSON.stringify(obj));
}

function submitOnClick(identifier, startTime) {
	var changepoints = getChangepoints();
	if (changepoints.length === 0) {
		$('#NoCPYesCPModal').modal();
		return false;
	}

    if (!validateDifficulty()) {
        return;
    }

    if (!askForProblem(submitOnClick, identifier, startTime)) {
        return;
    }

	var difficulty = document.querySelector('input[name="difficulty"]:checked');

	var obj = {};
	obj["identifier"] = identifier;
	obj["difficulty"] = difficulty.value;
	obj["changepoints"] = [];
	obj["time_spent"] = new Date() - startTime;
    obj["problem"] = document.getElementById('problem-text').value;

	var i, cp, xval, seen = [];
	for (i=0; i<changepoints.length; i++) {
		cp = changepoints[i];
		xval = cp.getAttribute("data_X");
		elem = {
			id: i,
			x: xval,
			t: cp.classList[0]
		};
		if (seen.includes(xval))
			continue;
		obj["changepoints"].push(elem);
		seen.push(xval);
	}

	var xhr = new XMLHttpRequest();
	xhr.open("POST", "");
	xhr.withCredentials = true;
	xhr.setRequestHeader("Content-Type", "application/json");
	/* Flask's return to this POST must be a URL, not a template!*/
	xhr.onreadystatechange = function() {
		if (xhr.readyState == XMLHttpRequest.DONE && xhr.status == 200) {
			window.location.href = xhr.responseText;
		}
	};
	xhr.send(JSON.stringify(obj));
}