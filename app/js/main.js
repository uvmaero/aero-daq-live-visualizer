// maximums for speed and current graphs
// TODO: pull these from a config file
var MAX_SPEED = 80;
var MAX_CURRENT = 360;

// range for cell temps
// TODO: pull these from a config file
var CELL_TEMP_MAX = 65;
var CELL_TEMP_MIN = 10;
var CELL_TEMP_RANGE = CELL_TEMP_MAX - CELL_TEMP_MIN;

// refresh rate, in hertz. The server will be polled this often
var REFRESH_RATE = 1;

// update timer for pulling data from the server
var updateTimer;

// pause state
var paused = false;

// vehicle name (span in the header text)
var vehicleName;

// Epoch live charts for data visualization
var throttleGauge;
var speedGauge;
var currentGauge;
var socGauge;
var cellVoltChart;

// initial data for the cell voltage chart
var cellVoltInitial = [
    {
        label: "maximum",
        values: [{time: Date.now()/1000, y: 3.6}]
    },
    {
        label: "minimum",
        values: [{time: Date.now()/1000, y: 3.6}]
    },
    {
        label: "average",
        values: [{time: Date.now()/1000, y: 3.6}]
    }
];

/**
 * Returns the maximum value in an array
 * @param {float array} arr 
 */
function arrayMax(arr) {
    var max = arr[0];
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
}

/**
 * Returns the minimum value in an array
 * @param {float array} arr 
 */
function arrayMin(arr) {
    var min = arr[0];
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] < min) min = arr[i];
    }
    return min;
}

/**
 * Returns the average of the items in an array
 * @param {float array} arr 
 */
function arrayAvg(arr) {
    var sum = 0;
    for (var i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    return sum/arr.length;
}

/**
 * Update Handler
 * 
 * Updates UI with new data from the server using AJAX. Server responds to a POST
 * request on /get_data with a json blob containing the newest data.
 */
function updateHandler() {
    // construct an AJAX request to get_data
    $.ajax({
        url: "/get_data",
        method: "POST",
        success: function(result) {
            // convert received string into a json object
            data = JSON.parse(result);

            // update the vehicle name in the page title
            vehicleName.text(data["vehicle_name"]);

            // push the new throttle value to the throttle gauge
            throttleGauge.push(data["throttle"]);

            // push the new current value to the current gauge
            currentGauge.push(data["current"])

            // push the new current value to the current gauge
            speedGauge.push(data["speed"])

            // push the new current value to the current gauge
            socGauge.push(data["soc"])

            // get min, max, and average cell voltages
            cellVoltMax = arrayMax(data["cell_volt"]);
            cellVoltMin = arrayMin(data["cell_volt"]);
            cellVoltAvg = arrayAvg(data["cell_volt"]);

            // create the entry for the cell voltage chart
            var cellVoltEntry = [];
            cellVoltEntry.push({time: data["timestamp"]/1000, y: cellVoltMax});
            cellVoltEntry.push({time: data["timestamp"]/1000, y: cellVoltMin});
            cellVoltEntry.push({time: data["timestamp"]/1000, y: cellVoltAvg});

            // push the entry to the cell voltage chart
            cellVoltChart.push(cellVoltEntry);
            
            // Update the cell temperature display
            for (var i=0; i < data["cell_temp"].length; i++) {
                // normalize the temperature to [0, 1], because that's what colormaps need
                var temp_normalized = (data["cell_temp"][i] - CELL_TEMP_MIN) / CELL_TEMP_RANGE;
                
                // interpolate the "jet" colormap with the normalized temperature
                rgb = interpolateLinearly(temp_normalized, jet);

                // split the rgb array into red, green, and blue components
                var r = rgb[0] * 255;
                var g = rgb[1] * 255;
                var b = rgb[2] * 255;

                // update the cell display with the new background color and its temperature
                $("#cell"+i).css("background", "rgb("+r+","+g+","+b+")").text(data["cell_temp"][i] + " C");
            }
        }
    });
}

// This will run on page load
$(function() {
    // get vehicle name element
    vehicleName = $('#vehicleName');

    // set the click handler for the pause button
    $('#pauseButton').click(function() {
        if (!paused) {
            // if not paused, stop the update timer
            clearInterval(updateTimer);
            paused = true;

            // change the text to "Run"
            pauseButton.text("Run");
        } else {
            // if paused, set the update timer
            updateTimer = setInterval(updateHandler, 100);
            paused = false;

            // change the text to "Pause"
            pauseButton.text("Pause");
        }
    });

    // initialize the throttle gauge
    throttleGauge = $('#throttleGauge').epoch({
        type: 'time.gauge',
        value: 0,
        speed: REFRESH_RATE
    });

    // initialize the speed gauge
    speedGauge = $('#speedGauge').epoch({
        type: 'time.gauge',
        value: 0,
        domain: [0, MAX_SPEED],  // speed ranges from 0 to 80mph
        format: function(v) { return Math.round(v) + 'mph'; },
        speed: REFRESH_RATE
    });

    // initialize the current gauge
    currentGauge = $('#currentGauge').epoch({
        type: 'time.gauge',
        value: 0,
        domain: [0, MAX_CURRENT],
        format: function(v) { return Math.round(v) + 'A'; },
        speed: REFRESH_RATE
    });

    // initialize the state of charge gauge
    socGauge = $('#socGauge').epoch({
        type: 'time.gauge',
        value: 0,
        speed: REFRESH_RATE
    });

    // initialize the cell voltage chart
    cellVoltChart = $('#cellVoltChart').epoch({
        type: 'time.line',
        data: cellVoltInitial,
        axes: ['left', 'bottom']
    });

    // Setup update handler to run at a rate of REFRESH_RATE
    updateTimer = setInterval(updateHandler, 1000/REFRESH_RATE);
});