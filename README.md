# ResearchDoom and CocoDoom

This code release supports the *ResearchDoom* platform. It contains a modified *Doom* engine that can be used to record annotated data from games, some MATLAB functions to easily parse this data, and functions and scripts to reproduce the *CocoDoom* dataset.

> You *do not need* this code if all you want is to use the pre-computed *CocoDoom* data. You need this only if you want to record new data. Some of the MATLAB functions, however, can be useful in general.

## Installation

This version of ResearchDoom uses a fork of `chocolate-doom` as main engine. This fork  can record the Doom game frames as well as depth map and object map information during gameplay. Make sure to install this and all other third-party code using

      git submodule update -i

Then:

* Compile the code in `engines/chocolate`. Check the instructions therein to see how.

* Download the Doom WAD (game) files and store them in e.g. `data/wads`. For CocoDoom, you will need the `doom2.wad` version.

## Recording data

Use the script `engines/chocolate/rdm-record.sh` to extract data from recorded gaming sessions. Either record your own game or download wad files from the Internet. Games are recorded as `.lmp` files and are several collections can be found [online](http://doomedsda.us/wad945m240.html). Use:

     engines/chocolate/rdm-record.sh WADFILE LMPFILE OUTDIR

to save all frames and corresponding annotations to the folder `OUTDIR`.

The code offers a large number of additional options to tune the output. It is also possible to record as you play.

## CocoDoom

Generating the CocoDoom data from scratch is a multi-step approach:

1. Use `scripts/cocodoom-record.sh` to extract the raw *CocoDoom* data using the `engines/chocolate/bin/doom` game engine.

2. Use `matlab/genCocoData.m` to extract the CocoDoom annotation files from the raw data.

3. Use `matlab/splitCocoData.m` to generate the various data splits.

4. Use `scripts/cocodoom-pack.sh` to generate the `.tar.gz` archives.

The main conversion script is `makeCocoData.m`. This can take the output of `engines/chocolate/rdm-record.sh` and extract a JSON annotation file compatible with the MS Coco API. Please look at the function header in this file for documentation on how to use it. This function will take several hours if run on a long demo.

### Train-val-test splits

Recommended train-val-test splits are defined in the `./trainvaltest` folder. Two splits are provided based on data extracted using three speed demos. The first split is splitting across demos by different users but covering all the same game levels. The second split is across game levels. The latter is more challenging because it has different content in training, test and validation. See below for downloading the actual images for these splits.

