# Research software for mapping the techno-economic landscape for the carbon abatement of hard-to-electrify sectors.
## Overview
This research software was used to obtain results for the article **Mapping the techno-economic landscape for the carbon abatement of hard-to-electrify sectors** (link and DOI TBC).

It performs a techno-economic analysis of different abatement options for the hard-to-electrify (HTE) sectors: steel, cement, chemical feedstocks, international aviation and international transport. The levelized cost of different products (LCOPs) and the fuel-switching CO2 price (FSCP) are then obtained, and plotted in different figures.

All assumptions used for the calculations are contained in the src/calc folder, in the `params.json` file. For more details on the literature used to derive these assumptions, the reader is referred to the article.

## How to use this software

### Installing dependencies

In order to execute this software, the corresponding python dependencies have to be installed. The use of poetry is here recommended, using:

```
poetry install
```

### Replicating figures

To replicate the figures generated in this software, once the virtual environment has been activated, use:

```
python export_figs.py
```
This will generate all figures, including the supplementary figures.

### Re-calculating heat map data

The heat map data used is contained in the `data` folder. This can be re-calculated (for example if parameters have been changed) by running:

```
python calc_hmdata.py
```
This script takes between 2 minutes and 20 minutes to run, dependent on the parameters chosen.

### Interactive webapp

A webapp associated with this work can be found [here](https://github.com/clarabachorz/abating-hte-sectors-webapp), to interactively view the detail of the technoeconomic assumptions taken, and the different levelized cost components.

## How to cite this work

Bachorz, Clara Z.; Verpoort, Philipp C.; Ueckerdt, Falko: Research software for mapping the techno-economic landscape for the carbon abatement of hard-to-electrify sectors.

## License
The code contained in this repository is available for use under an [MIT license](https://opensource.org/license/mit).