# Research software for exploring techno-economic landscapes of abatement options for hard-to-electrify sectors.
## Overview
This research software was used to obtain results for the article **Exploring techno-economic landscapes of abatement options for hard-to-electrify sectors** (link and DOI TBC).

It performs a techno-economic analysis of different abatement options for the hard-to-electrify (HTE) sectors: steel, cement, chemical feedstocks, international aviation and international transport. The levelized cost of different products (LCOPs) and the fuel-switching CO2 price (FSCP) are then obtained, and plotted in different figures.

All assumptions used for the calculations are contained in the src/calc folder, in the `params.json` file. For more details on the literature used to derive these assumptions, the reader is referred to the article.

## How to use this software

### System requirements

This software can be ran on a standard computer, capable of running standard Python scripts. Ideally, a computer that has a multi-core processor should be used, to allow multiprocessing (as used in the `calc_data` script). 
All major operating systems can be used (Windows, MacOS or Linux), although this software has only been tested on Windows 10.

### Installing python dependencies

This code has been tested and developed with Python 3.11. In order to execute this software, the corresponding python dependencies have to be installed. The use of poetry is recommended here, using:

```
poetry install
```

Installing these dependencies (excluding python and poetry) takes between 10 to 20 seconds.

### Replicating figures

To replicate the figures generated in this software, once the virtual environment has been activated, use:

```
python export_figs.py
```
If the initial data files have not been changed by the user (see below), this will generate all paper figures, including the supplementary figures, as pngs in the `figs` file. This takes about 5 minutes to run on the default figure resolution.

### Re-calculating heat map data

The heat map data used is contained in the `data` folder. This can be re-calculated for different techno-economic parameters, as defined by the user. The standard parameters used, that are detailed in the Supplementary Information of the paper, can be found  in the `calc\params.json` file. To run the full techno-economic calculation for new parameters, the user should first change the json file, before running:

```
python calc_hmdata.py
```
This script will update every csv files in the `data` folder. It takes between 2 minutes and 20 minutes to run, dependent on the parameter resolution chosen for the heat maps (defined, for example in the main figure, by the parameters in the function `mainfig_params()` in `calc_hmdata`).

### Interactive webapp

A webapp associated with this work can be found [here](https://github.com/clarabachorz/mapping-hte-sectors-webapp), to interactively view the detail of the technoeconomic assumptions taken, and the different levelized cost components.

## How to cite this work

Bachorz, Clara; Verpoort, Philipp C.; Ueckerdt, Falko; Luderer, Gunnar: Research software for exploring techno-economic landscapes of abatement options for hard-to-electrify sectors.

## License
The code contained in this repository is available for use under an [MIT license](https://opensource.org/license/mit).
