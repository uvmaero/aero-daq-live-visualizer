const electron = require('electron');  // electron is used for creating the window for the app
const exec = require('child_process').exec;  // child process is used for launching the server
const request = require('ajax-request')  // ajax-request is used for shutting down the server via HTTP

const { app, BrowserWindow } = electron;

let mainWindow;

// create electron app
app.on('ready', () => {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        webPreferences: {
            nodeIntegration: false
        }
    });

    mainWindow.setTitle('AERO Live Data Visualizer');
    mainWindow.loadURL('http://localhost:8000');

    // First launch the server
    server = exec('twistd -y server.py -n', {cwd: 'server'});

    mainWindow.on('closed', () => {
        mainWindow = null;
        request({
            url: "http://localhost:8000/close",
            method: "POST",
        }, function() {});
    });
});