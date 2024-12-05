import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors
import matplotlib.patches as patches
from  matplotlib.cm import ScalarMappable
from pathlib import Path
import string

from src.plot import common

SMALL_SIZE = 18
MEDIUM_SIZE = 20
BIGGER_SIZE = 22

plt.rc('font', size=MEDIUM_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title



def plot_heatmap(data, cmap, ax, cbar, vmin=0, vmax=1, rasterized=True):
    return sns.heatmap(data, cmap=cmap, cbar = cbar, vmin=vmin, vmax=vmax, ax=ax, rasterized=rasterized)

def add_rectangle(ax, xcoord, ycoord, w, h):
    ax.add_patch(
        patches.Rectangle(
            (xcoord, ycoord),
            w,
            h,
            edgecolor='#3b3b3b',
            fill=True,
            # fc=(0.7, 0.7, 0.7, 0.15),
            fc=(0.7, 0.7, 0.7, 0.2),
            lw=1.5,
        )
    )

def add_annotation(ax, text, xcoord, ycoord):
    ax.annotate(text, xy=(xcoord, ycoord), fontsize=SMALL_SIZE, ha='center', va='center_baseline', color="#3b3b3b")

def return_custom_cmap(mapping_dict):
    color_dict = common.color_dict_tech
    dict_cmap = {value: color_dict[key] for key, value in mapping_dict.items()}
    custom_cmap = matplotlib.colors.ListedColormap([dict_cmap[key] for key in sorted(mapping_dict.values())])
    return custom_cmap

def return_transparent_cmap():
    #second cmap: transparency cmap
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["white","white","white"])
    # Get the colormap colors
    transparent_cmap = cmap(np.arange(cmap.N))
    # linear transparent colormap:
    transparent_cmap[:,-1] =np.linspace(0, 1, cmap.N)[::-1]
    # Create new colormap
    transparent_cmap = matplotlib.colors.ListedColormap(transparent_cmap)
    return transparent_cmap

def make_multiple_cbars(ax, row, cmap_list, defaultcmap_ticks):
    # Colorbar setting: currently, first and second row consider all options (including full DACCS)
    # third row does not, and the colorbar used changes. Full climate neutrality is also required,
    # so all options are complemented with DACCS
    colorbar = ax.collections[0].colorbar
    if colorbar is not None:
        ticklabels = ['H2/NH3\n+ CDR', 'E-fuel\n+ CDR', 'CCU\n+ CDR', 'CCS\n+ CDR'] if cmap_list[row] is not None else defaultcmap_ticks

        # Calculate tick positions
        step = 1.0 / (len(ticklabels))
        ticks = np.arange(0+ step/2, 1 + step/2, step)

        colorbar.set_ticks(ticks)
        colorbar.set_ticklabels(ticklabels)
        colorbar.ax.tick_params(labelsize=MEDIUM_SIZE) 


def make_default_cbar(fig, defaultcmap, defaultcmap_ticks):
    #create additional space to the right of the figure
    #cbar_ax = fig.add_axes([0.92, 0.2, 0.02, 0.5])
    #or at the bottom of the figure (need to then add orientation = "horizontal")
    cbar_ax = fig.add_axes([0.28, -0.03, 0.5, 0.02])
    colorbar = fig.colorbar(ScalarMappable( cmap=defaultcmap), cax = cbar_ax, orientation = "horizontal")

    # Calculate tick positions
    step = 1.0 / (len(defaultcmap_ticks))
    ticks = np.arange(0+ step/2, 1 + step/2, step)

    colorbar.set_ticks(ticks)
    colorbar.set_ticklabels(defaultcmap_ticks)
    colorbar.ax.tick_params(labelsize=MEDIUM_SIZE)

def plot_sectoral_hm(path_to_data, rowvar_name, row_vars, row_titles, x_var = "co2_LCO", y_var = "h2_LCO", cmap_list = None, vmax_hmdiff=100, fig_title = '', figsize=(20,20)):
    """
    rowvar_name: name of the variable that will be used to create the different rows
    row_vars: list of the different values that the rowvar_name can take (defines the number of rows)
    row_titles: list of the titles that will be used for each row
    x_var, y_var: name of the variables that will be used for the x and y axis
    cmap_list: list of custom color maps to be used for each row of the heatmaps. 
                If None, the default color map will be used, with only one color bar
                on the right hand side of the plot.
    fig_title: name of the figure that will be saved
    """
    # import plotting parameters from common
    # color_dict_tech = common.color_dict_tech
    rename_sectors = common.rename_sectors

    #associate type of technology to discrete value
    dict_type_ID = {"h2": 0, "efuel": 0.25, "comp":0.5, "ccu":0.75, "ccs":1}
    #dict_type_ID = {"h2": 0, "blueh2":0.2, "efuel": 0.4, "comp":0.6, "ccu":0.8, "ccs":1}

    #make custom heatmaps based on the technologies available
    defaultcmap = return_custom_cmap(dict_type_ID)
    transparent_cmap = return_transparent_cmap()

    # define default ticks for the colorbar
    # defaultcmap_ticks = ['H2/NH3', 'Blue\nH2/NH3', 'E-fuel','DACCS\ncompen-\nsation', 'CCU', 'CCS']
    defaultcmap_ticks = ['H2/NH3', 'E-fuel','Compen-\nsation', 'CCU', 'CCS']

    #load data 
    df_fig = pd.read_csv(path_to_data) 
    #remove the first two columns, which are just old indice
    df_fig = df_fig.iloc[:,2:]
    #add values to identify the categories in the heat map, using the appropriate dict
    df_fig["type_ID"] = df_fig["type"].map(dict_type_ID)

    ### MAKE fighm ###
    # colvar is fixed, and is the sector
    # the other vars (col_var, x_var, y_var) are arguments of the function
    colvar_name = "sector"

    #other list and dictionnaries used for plotting
    col_vars = ["chem", "plane", "ship", "steel", "cement"]

    rows = len(row_vars)
    cols = len(col_vars)

    # define figure size
    #fig, axs = plt.subplots(nrows=len(row_vars), ncols=len(col_vars), figsize=(4*len(col_vars),4*len(row_vars)), constrained_layout=True)
    fig, axs = plt.subplots(nrows=len(row_vars), ncols=len(col_vars), figsize=figsize, constrained_layout=True)
    for row in range(len(row_vars)):
        #select the appropriate row var
        row_var = row_vars[row]
        #filter data accordingly
        sub_df = df_fig.loc[df_fig[rowvar_name] == row_var].reset_index(drop=True)

        #add row title, on the left hand side. As defined by "scenario name" variable
        for col in range(len(col_vars)):
            ax = axs[row, col]
            pad = 18
            if col == 0:
                ax.annotate(f'{row_titles[row]}',
                            xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
                            xycoords=ax.yaxis.label, textcoords='offset points',
                            ha='center', va='center', ma= "center", rotation = 90, fontsize = BIGGER_SIZE)
                ax.text(-0.3, 1, string.ascii_lowercase[row], transform=ax.transAxes, 
                    size=18, weight='bold')

            #get the correct column variable
            col_var = col_vars[col]

            #again, filter the data to find the appropriate portion
            sub_sub_df = sub_df.loc[sub_df[colvar_name] == col_var].reset_index(drop=True)
            
            # create the dfs that will be used for the heat map
            # one with the sectoral color, one for the transparent layer, one for the fscp contour
            sns_df = sub_sub_df.pivot(index = y_var, columns = x_var, values="type_ID")
            sns_diff_df = sub_sub_df.pivot(index = y_var,columns = x_var, values = "delta_fscp")
            contour_df = sub_sub_df.pivot(index = y_var, columns = x_var, values = "fscp")

            if cmap_list is None:
                #plot the default sectoral color heat map:
                heatmap_cmap = defaultcmap
                heatmap = plot_heatmap(sns_df, heatmap_cmap, ax, cbar = None, rasterized=True)
                
                #colorbar function: only run on the last step
                # one colorbar for the whole figure, shown on the right
                if row == rows-1 and col == cols-1:
                    make_default_cbar(fig, defaultcmap, defaultcmap_ticks)
            else:
                #plot the customized sectoral color heat map, which has multiple colorbars
                # (one per row)
                heatmap_cmap = cmap_list[row] if cmap_list[row] is not None else defaultcmap
                heatmap = plot_heatmap(sns_df, heatmap_cmap, ax, cbar = (col == cols-1)&(row >= 0), rasterized=True)
                #make the colorbars
                make_multiple_cbars(ax, row, cmap_list, defaultcmap_ticks)

            # add the additional transparent layer to show the fscp difference between the first and second minima
            # the default heatmap only shows this difference, with a white shading, up to an FSCP diff of 100.
            # this can be changed directly in the function parameter
            heatmap_diff = plot_heatmap(sns_diff_df, transparent_cmap, ax, cbar = False, vmin=0, vmax=vmax_hmdiff)
            # and the contour line
            contour_values = {"steel": [0, 50, 100, 150, 200,250], "cement": [0,50, 100, 150, 200, 250], "plane":[0, 500, 1000, 1500, 2000]}.get(col_var, [0, 400, 800, 1200, 1600])
            contour = ax.contour(np.arange(.5, contour_df.shape[1]), np.arange(.5, contour_df.shape[0]), contour_df, contour_values, colors='#3b3b3b', alpha=0.8, linewidths=0.8)

            #change contour label params
            ax.clabel(contour, inline=True, fontsize=SMALL_SIZE)

            #add the rectangles to show the 2022 and 2050 regions
            # our assumptions for 2050: CO2 cost between 80 (used to be 200 for DAC) and 800 EUR/tCO2, h2 cost between 57 and 180 EUR/MWh
            # our assumptions for 2022: CO2 cost between 900 and 1200 EUR/tCO2, h2 cost between 120 and 240 EUR/MWh
            co2_2050_xcoord = (np.abs(sns_df.columns.to_numpy() - 80)).argmin()
            h2_2050_ycoord = (np.abs(sns_df.index.to_numpy() - 57)).argmin()
            co2_2050_w = (np.abs(sns_df.columns.to_numpy() - 800)).argmin() - co2_2050_xcoord
            h2_2050_h = (np.abs(sns_df.index.to_numpy() - 180)).argmin() - h2_2050_ycoord

            co2_2022_xcoord = (np.abs(sns_df.columns.to_numpy() - 900)).argmin()
            h2_2022_ycoord = (np.abs(sns_df.index.to_numpy() - 120)).argmin()
            co2_2022_w = (np.abs(sns_df.columns.to_numpy() - 1200)).argmin() - co2_2022_xcoord
            h2_2022_h = (np.abs(sns_df.index.to_numpy() - 240)).argmin() - h2_2022_ycoord

            # Draw the rectangle patches
            add_rectangle(ax, co2_2050_xcoord, h2_2050_ycoord, co2_2050_w, h2_2050_h)
            # add_rectangle(ax, co2_2022_xcoord, h2_2022_ycoord, co2_2022_w+1, h2_2022_h+1)

            # Add annotations
            add_annotation(ax, ">2050", co2_2050_xcoord + co2_2050_w/2 +5, h2_2050_ycoord-5)
            # add_annotation(ax, "2022", co2_2022_xcoord+co2_2022_w/2, h2_2022_ycoord-5)

            # change x and y parameter ticks manually
            ax.locator_params(axis='x', nbins=11)

            # Get unique y_var values and sort them
            y_var_unique = np.sort(sub_sub_df[y_var].unique())
            no_yvars = len(y_var_unique)

            # Set y-ticks at equally spaced intervals
            y_ticks = np.linspace(0, no_yvars-1, 7)
            ax.set_yticks(y_ticks)

            # Set y-tick labels at corresponding y_var values
            y_ticklabels = np.round(np.linspace(y_var_unique[0], y_var_unique[-1], len(y_ticks)), 0).astype(int)
            ax.set_yticklabels(y_ticklabels)

            ax.invert_yaxis()

            if y_var == "h2_LCO":
                # Add a secondary axis for H2, to show the cost in EUR/kg
                ax2 = ax.twinx()
                h2tck = y_var_unique / 30

                ax2.set_yticks(ax.get_yticks())
                ax2_yticklabels = np.round(np.linspace(min(h2tck), max(h2tck), len(ax.get_yticks())),1)
                ax2.set_yticklabels(ax2_yticklabels, fontsize=SMALL_SIZE)

            
            # Additional aesthetics: labels, titles, etc.
            if col == 0:
                ax.set_ylabel('Low-emission H2 cost (EUR/MWh)', fontsize = SMALL_SIZE)
                ax2.set_yticklabels([])
            elif col == cols-1:
                ax2.set_ylabel("Low-emission H2 cost (EUR/kg)\n", fontsize = SMALL_SIZE)
                ax.set_ylabel("")
                ax.set_yticklabels([])
            else:
                ax.set_ylabel("")
                ax.set_yticklabels([])
                ax2.set_yticklabels([])
            
            if row == 0 :
                ax.set_title(rename_sectors[col_var], fontsize = BIGGER_SIZE)
                ax.set_xlabel("")
                ax.set_xticklabels([])
            elif row == rows-1:
                ax.set_xlabel('Non-fossil CO2 cost\n(EUR/tCO2)', fontsize = SMALL_SIZE)
            else: 
                ax.set_xlabel("")
                ax.set_xticklabels([])

    # tight layout needs to be adjusted depending on whether we have one big colorbar, or multiple small ones
    if cmap_list is None:
        #fig.get_layout_engine().set(w_pad=4 / 72, h_pad=4 / 72, hspace=0, wspace=0, rect=[0, 0, .9, 1])
        fig.get_layout_engine().set(w_pad=4 / 72, h_pad=4 / 72, hspace=0, wspace=0, rect=[0, 0, 1, .9])
    else:
        fig.get_layout_engine().set(w_pad=4 / 72, h_pad=4 / 72, hspace=0, wspace=0)

    # currently not needed
    # if cmap_list is not None:
    #     fig.get_layout_engine().set(w_pad=4 / 72, h_pad=4 / 72, hspace=0, wspace=0)
    # for n, ax in enumerate(axs):   
    #     ax.text(-0.1, 1.05, string.ascii_lowercase[n], transform=ax.transAxes, 
    #             size=18, weight='bold')
    for ax in axs.flatten():
        plt.setp(ax.get_yticklabels(), fontsize=SMALL_SIZE)
        plt.setp(ax.get_xticklabels(), fontsize=SMALL_SIZE)
        #fig.savefig('./analysis/fig/fscp_hm.svg', format='svg', dpi=1200)
    figpath = r"././figs/" + fig_title + ".png"
    fig.savefig(figpath, format='png', dpi=600, bbox_inches='tight')


def plot_mainfig():
    row_vars = ["normal","ccu", "comp"]
    row_titles = ["No conditions\n", "Fossil CCU: CO2 utilization\nrequires CO2 source\n", "Compatibility with climate\nneutrality (compensation\nof residual emissions)\n\n"]
    
    cmap_list = None
    plot_sectoral_hm(#path_to_data='./data/figfscp_rawdata.csv',
                    path_to_data = str(Path(__file__).parent.parent / '../data/mainfig_rawdata.csv'),
                    rowvar_name="scenario", 
                    row_vars = row_vars, 
                    row_titles= row_titles,
                    cmap_list = cmap_list,
                    fig_title = 'main_HTElandscapes')
    
    plot_sectoral_hm(path_to_data = str(Path(__file__).parent.parent / '../data/supCCUattrib_rawdata.csv'),
                    rowvar_name="scenario", 
                    row_vars = row_vars, 
                    row_titles= row_titles,
                    cmap_list = cmap_list,
                    vmax_hmdiff=20,
                    fig_title = 'supp_HTElandscapeshighCCUattrib')

def plot_supfig():
    row_vars = [8,30,100,200]
    row_titles = [f'CO2 transport and storage cost:\n {num} EUR/tCO2\n\n' for num in row_vars]

    plot_sectoral_hm(#path_to_data='code_figS3/figS2_rawdata.csv',
                    path_to_data = str(Path(__file__).parent.parent / '../data/sup_rawdata.csv'),
                    rowvar_name="co2ts_LCO", 
                    row_vars = row_vars, 
                    row_titles= row_titles,
                    fig_title = 'supp_HTElandscapesCO2ts',
                    figsize=(20,25))
    #plt.show()