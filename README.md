# AERO DAQ Live Data Visualizer

## AERO DAQ
AERO DAQ is a University of Vermont Engineering Capstone Project (SEED) team for the 2018-2019 academic year that is desiging a data acquisition system (DAQ) for AERO (Alternative Energy Racing Organization). The team consists of Senior AERO members Cullen Jemison, Jack Zimmerman, Peter Ferland, and Ryan Chevalier.

## Purpose
This program serves as the live frontend to the AERO DAQ project. It displays select data that is remotely transmitted from the car to a set of gauges and graphs. It allows for team members in the pit to view the current status of the car so they can inform the driver of any changes that need to be made to their driving style.

## Structure
The program consists of a Python server using [Twisted](https://github.com/twisted/twisted) and a frontend/web GUI written in Javascript/HTML that utilizes the [Epoch](https://github.com/epochjs/epoch) live graphing library to generate the gauges and graphs.

The Python server directly reads data from the car and presents a network endpoint that returns a single large JSON blob containing all the data when accessed via HTTP POST.

The Javascript frontend uses AJAX to request data from the server on a regular interval. The JSON data is parsed and used to update all the graphs and gauges on the page.