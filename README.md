# ResearchDoom and CocoDoom

The *ResearchDoom* project aims to extract data and ground-truth annotations from the Doom game for the purpose of training and evaluating computer vision algorithms. For more information, see the project [homepage](http://www.robots.ox.ac.uk/~vgg/research/researchdoom/).

This software package supports the *ResearchDoom* platform. It contains a modified *Doom* engine that can be used to record annotated data from games, some Python (and MATLAB) functions to easily parse this data, and functions and scripts to reproduce the *CocoDoom* dataset.

> You *do not need* this code if all you want is to use the pre-computed *CocoDoom* data. You need this only if you want to record new data. Some of the Python (and MATLAB) functions, however, can be useful in general.

The code is made available under a pseudo-BSD [license](COPYING).

## Installation

This version of ResearchDoom uses a fork of `chocolate-doom` as its main engine. This fork can record Doom game frames as well as depth-map and object-map information during gameplay. Make sure to install this and all other third-party dependencies using

```shell
git submodule update -i
```

The Doom engine in `engines/chocolate` needs to be compiled, which in turn requires additional dependencies. On macOS, the easiest way to install them and compile the code is to use brew:

```shell
brew install sdl2 sdl2_mixer sdl2_net libsamplerate libpng fluid-synth
cmake -S engines/chocolate -B engines/chocolate/build -G Ninja
cmake --build engines/chocolate/build --target chocolate-doom
```

Check the [instructions therein](http://www.github.com/vlfeat/researchdoom-chocolate) to see further details on how to compile the engine.

If you wish to use the modern Python version of CocoDoom, you will also need a suitable Python environment.

```shell
brew install uv
uv sync --directory python
```

You will need the Doom WAD game files and should store them in, for example, `data/wads`. For CocoDoom, you will need version 1.9 of `doom2.wad`.

You can test the installation by recording one run:

```shell
source python/.venv/bin/activate
PYTHONPATH=python python3 -m rdm.rdm dataset=cocodoom_run1
```

## Recording game data

Use the script `engines/chocolate/rdm-record.sh` to extract data from recorded gaming sessions. Either record your own game or download WAD files from the Internet. Games are recorded as `.lmp` files, and several collections can be found [online](http://doomedsda.us/wad945m240.html). Use:

```shell
engines/chocolate/rdm-record.sh WADFILE LMPFILE OUTDIR
```

to save all frames and corresponding annotations to the folder `OUTDIR`.

The code offers a large number of additional options to tune the output. It is also possible to record as you play.

## CCTV Doom

CCTV Doom for now only supports extracting the raw Doom data from multiple cameras defined in the configuration files. These cameras must then be manually defined for each game map (e.g,. Doom e1m1) and added to files like `python/rdm/config/dataset/cctvdoom_run1.yaml`. Then this code can be used to generate the data for such a run:

```shell
source python/.venv/bin/activate
PYTHONPATH=python python3 -m rdm.rdm dataset=cctvdoom_run1
```

Make sure that these runs only involve *one* Doom map (some runs as the ones used in CocoDoom below run through the entire game). This is required as the camera definitions only make sense for that one map.

Add more runs to the script `scripts/cctvdoom_generate.sh` for reproducibility.

The script `rdm_get_warp.py` contains code to reconstruct the camera matrices from the position and orientation of the camera as defined in Doom.

## CocoDoom

To generate the CocoDoom data from scratch, use the script `scripts/cocodoom-generate.sh`. This will generate the CocoDoom data in `/tmp/cocodoom`.

Default train-val-test splits are defined as:

```text
map-full-test.json
map-full-train.json
map-full-val.json
map-test.json
map-train.json
map-val.json
run-full-test.json
run-full-train.json
run-full-val.json
run-test.json
run-train.json
run-val.json
```

Two splits, `run` and `map`, are provided based on data extracted from three speed demos. The first split is across runs (demos) by different users while covering the same game levels. The second split is across game maps (levels). The latter is more challenging because it contains different content in training, validation, and test. Each split exists both in a shorter variant, where frames are skipped, and in the `full` variant, which retains all frames.

## CocoDoom (legacy version)

Historically, CocoDoom was built on MATLAB rather than Python. You can still run the legacy code using Octave as a free alternative:

```shell
brew install octave
octave --quiet --eval "pkg install -forge image datatypes"
./scripts/cocodoom-legacy/cocodoom-extract.sh
```

## Changes

* July 2026: Full rewrite of the engine in Python and initial support for CCTV-Doom.
