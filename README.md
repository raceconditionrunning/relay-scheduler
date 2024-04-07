# relay-scheduler

An [Answer Set Programming](https://en.wikipedia.org/wiki/Answer_set_programming) domain for scheduling relay events. Originally created for our [Light Rail Relay 2021 event](http://raceconditionrunning.com/light-rail-relay/).

* Schedules from scratch 
* ...or give a sketch and have the solver fill in the rest
* Customize race format (e.g. number of runners per leg, minimum distance)
* Configurable optimization for total duration or matching runner preferences for distance, pace, or end exchange. Use multiple objectives lexicographically
* Consumes legs specified as GPX files


## Usage

Get a working installation of [Clingo](https://github.com/potassco/clingo) >=5.5. Potassco's Anaconda channel makes this easy, or you can make a virtual env and install from requirements.txt

For Apple Silicon Macs, use Homebrew and ensure you install cffi in the correct version of Python, e.g. `python3.12 -m pip install cffi`.

Specify your problem matching the format used in `lrr202X/lrr.lp`. 

Now:

    ./solve.py lrr2023

Use `--help` to see additional options.

Note that the solver will process float terms by converting them to a fixed precision (two decimal places, by default).
