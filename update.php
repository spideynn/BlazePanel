<?php

define GIT_PATH = "C:\\Git\\";
define PYTHON_PATH = "C:\\Python34\\";
// If we get a post from Github...
if ($_SERVER['REQUEST_METHOD'] === 'POST')
{    
    echo shell_exec(GIT_PATH + "git pull https://github.com/spideynn/blazegoat-panel.git"); //... git pull from the git repository with the specified git executable, then watchdog will reload python.
}
// First time setup, can be commented out later!
if ($_SERVER['REQUEST_METHOD'] === 'GET')
{
	echo "Setting up first time run..."
	echo shell_exec(PYTHON_PATH + "Scripts\\pip.exe install watchdog")
	echo shell_exec(PYTHON_PATH + "Scripts\\pip.exe install flask")
	echo shell_exec(PYTHON_PATH + "Scripts\\pip.exe install flask-login")
	echo shell_exec(PYTHON_PATH + "Scripts\\pip.exe install easygui")
	echo "Installed watchdog, flask, flask-login, easygui"
}