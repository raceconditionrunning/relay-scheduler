# relay-scheduler

An [Answer Set Programming](https://en.wikipedia.org/wiki/Answer_set_programming) domain for scheduling relay events. Originially created for our [Light Rail Relay 2021 event](http://raceconditionrunning.com/light-rail-relay/).

* Get schedules from scratch or pin some legs and have the solver fill in the rest
* Easy to customize your race format in terms of things like the number of runners per leg or allowable exchanges
* Configurable optimization for total duration or matching runner preferences for distance, pace, or end exchange. Use multiple objectives lexicographically
* Consumes legs specified as GPX files


## Usage

Get a working installation of [Clingo](https://github.com/potassco/clingo) >=5.5. Potassco's Anaconda channel makes this easy, or you can make a virtual env and install from requirements.txt

For Apple Silicon Macs, use homebrew and ensure you install cffi in the correct version of Python, e.g. `python3.11 -m pip install cffi'.

Specify your problem matching the format used in `202X/lrr.lp`. 

Now:

    python solve.py 202X

Note that the solver will process float terms by converting them to a fixed precision. By default, this is two decimal places.
