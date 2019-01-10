#!/bin/sh

if which xdg-open > /dev/null
then
  xdg-open "http://localhost:8000"
elif which gnome-open > /dev/null
then
  gnome-open "http://localhost:8000"
fi

cd server

twistd -y server.py -n