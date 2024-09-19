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

Solutions will stream into a timestamped folder in `solutions/`. By default, all optimal solutions are saved.

Use `--help` to see additional options.

Note that the solver will process float terms by converting them to a fixed precision (two decimal places, by default).

To view a solution, use 
    
        ./print_schedule.py solutions/<run>/solution.json

### Formatting Legs

A leg is a GPX file with a single track. The file is named `StartExchangeID-EndExchangeID.gpx`. The `<name>` tag should contain `Start Exchange Name to End Exchange Name`, and a `<desc>` tag with a summary of the leg.

### Formatting Participants

The participant file is a TSV with the following columns:

* `Name`
* `Pace` ("MM:SS", min/mi)
* `Distance` (mi)
* `PreferredEndExchange` exchange name, (optional)
* `Leader` whether participant wants to lead (optional, yes/no)

Loading participants from TSV is purely to make it easier to copy and paste from a spreadsheet; you can provide `participant/1` and preference facts manually if you prefer.

## Debugging and Extending

Running `solve.py` will output `facts.lpx` into the domain folder so you can check how any TSV/GPX specified facts were loaded.

In contrast with the facts output, the ground program has rules and simplifications applied. Inspecting the fully ground facts (solve with `--save-ground-facts`) can help you catch missing facts and bugged rules. 

`solve.py` is basically equivalent to `clingo --outf=0 --out-atomf=%s. scheduling-domain.lp domain/*.lp domain/facts.lpx`, so you can further debug using clingo-specific options. `--text` will output the full ground program (including expanded optimization directives).

You can use `print_schedule.py` to view a schedule table directly from raw clingo output. Call clingo with `clingo --outf=0 --out-atomf=%s. scheduling-domain.lp domain/*.lp domain/facts.lpx > solutions.txt` (note the important dot delimiter argument). Then run `print_schedule.py solutions.txt` to view the schedule.