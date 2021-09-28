# relay-scheduler

This is an [Answer Set Programming](https://en.wikipedia.org/wiki/Answer_set_programming) domain for scheduling relay events. The encoding was created for our [Light Rail Relay 2021 event](http://raceconditionrunning.com/light-rail-relay/).

* Get schedules from scratch or pin some legs and have the solver fill in the rest
* Easy to customize your race format in terms of things like the number of runners per leg or allowable exchanges
* Configurable optimization for total duration or matching runner preferences for distance, pace, or end station.
* Allows multiple optimization criteria with a defined order


## Usage

Get a working installation of [Clingo](https://github.com/potassco/clingo) >=5.5. Potassco's Anaconda channel makes this easy.

Specify your problem matching the format used in `lrr-2021.lp`. For now, you'll also need to manually update the list of files used in the bottom of the `solve.lp`. 

Now:

    clingo solve.lp

Note that the solver will process float terms by converting them to a fixed precision. By default, this is two decimal places.