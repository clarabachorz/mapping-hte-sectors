import numpy as np
import pandas as pd
import matplotlib
import string
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.colors import to_rgba
from matplotlib.ticker import FormatStrFormatter
import matplotlib.gridspec as gridspec
from  matplotlib.cm import ScalarMappable
import matplotlib.transforms as mtrans
from  matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.patches import Rectangle
from matplotlib.patches import FancyArrow, FancyArrowPatch, PathPatch
from matplotlib.lines import Line2D
from matplotlib.text import Text, TextPath

# plt.rcParams["font.family"] = "Calibri"
# plt.rcParams.update({
#     "text.usetex": True,
#     "font.family": "Helvetica"
# })

matplotlib.rcParams.update(matplotlib.rcParamsDefault)

#plot parameters, colors, text
rename_sectors = {"cement": "Cement\n", "steel" : "Steel\n", "ship" : "Maritime\n", "plane" : "Aviation\n", "chem" : "Chemical feedstocks\n(CF)" }
#ordering of technology types (h2, ccs, ccu etc)
order_types = ["fossil", "h2","blueh2", "efuel", "ccu", "ccs", "comp" ]
#colors
color_dict = {"cement":"#EABE7C", "steel":"#8c6570","ship":"#0471A6","plane":"#61E8E1", "chem":"#AFB3F7"}
# color_dict_tech = {"fossil":"#31393C", "h2": "#FCE762", "blueh2":"#0818A8", "efuel": "#FEB380", "comp":"#23CE6B", "ccu":"#8E9AAF", "ccs":"#3083DC"}
#below: color-blind friendly(er) palette
color_dict_tech = {"fossil":"#31393C", "h2": "#FCE762", "blueh2":"#0818A8", "efuel": "#FF9446", "comp":"#4C7D5B", "ccu":"#A5A9AF", "ccs":"#3083DC"}

sector_units = {"cement": "/t clinker", "steel" : "/t crude", "ship" : "/MWh", "plane" : "/PAX/km", "chem" : "/t olefin"}

#make nicer looking barplots
def change_spines(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#DDDDDD')

    # Second, remove the ticks as well.
    #ax.tick_params(bottom=False, left=False)

    # Third, add a horizontal grid (but keep the vertical grid hidden).
    # Color the lines a light gray as well.
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#EEEEEE')
    ax.xaxis.grid(False)
    return(ax)
#add colors defined above, units and sector description
def add_colors_units_rename(df):
    #add units and sector description
    df["unit"] = df["sector"].map(sector_units)
    df["sector_desc"] = df["sector"].map(rename_sectors)

    #add color columns
    df["color_sector"] = df["sector"].map(color_dict)
    df["color_type"] = df["type"].map(color_dict_tech)

    #add info column for plotting
    df["info"] = df["sector_desc"] + ": " + df["code"]
    return df
#sort data according to order defined above
def sort_data(df):
    # sort the data according to our custom order, defined in the plotting function
    df["type"] = pd.Categorical(df["type"], order_types)
    df = df.sort_values(by=["sector", "type"], ascending=[True, True])
    return df

def plot_large_panel_ccuattr(dfs):

    filtered_dfs = []
    for idx, df in enumerate(dfs):
        df = add_colors_units_rename(df)
        df = sort_data(df)
        #quick fix: remove blue H2
        df = df[df["type"] != "blueh2"]
        #We pick two sectors: here plane and cement
        df = df[df["sector"].str.contains("plane|cement") == True]
        df = df[df["type"].str.contains("ccu|ccs|comp") == True]
        #df = df.reset_index(drop = True)
        filtered_dfs.append(df)

    df_filtered = pd.concat([LCO_df for LCO_df in filtered_dfs]).drop_duplicates("fscp").reset_index(drop = True)
    df_filtered = df_filtered[df_filtered['fscp'].notna()]
    df_filtered = df_filtered[~((df_filtered['sector'] == 'cement') & (df_filtered['type'] == 'comp'))]

    
    custom_tech_order = {"ccs": 0, "ccu": 1, "comp": 2}
    df_filtered = df_filtered.sort_values(by = "co2ccu_co2em").sort_values(by = "type", key = lambda x: x.map(custom_tech_order)).reset_index(drop = True)

    df_filtered.loc[(df_filtered["type"] == "ccu")&(df_filtered["sector"] == "cement"), "info"] ="Cement\nCCU attr"+ df_filtered["co2ccu_co2em"].astype(str)
    df_filtered.loc[(df_filtered["type"] == "ccu")&(df_filtered["sector"] == "plane"), "info"] ="Aviation\nCCU attr"+ df_filtered["co2ccu_co2em"].astype(str)
    df_filtered.loc[df_filtered["type"] == "ccs", "info"] = "CCS"
    df_filtered.loc[df_filtered["type"] == "comp", "info"] = "CDR Compensation"

    cementccs_fscp = df_filtered[df_filtered["sector"] == "cement"].loc[df_filtered["type"] == "ccs", "fscp"].values[0]
    aviationcomp_fscp = df_filtered[df_filtered["sector"] == "plane"].loc[df_filtered["type"] == "comp", "fscp"].values[0]

    fig, ax = plt.subplots(figsize=(10, 8))

    SMALL_SIZE = 12
    MEDIUM_SIZE = 14
    BIGGER_SIZE = 16

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    plt.rc('axes', titlesize=BIGGER_SIZE)


    widths = [0.8,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.8]
    x_positions = [0,1.5,1.9,2.5,2.9,3.5,3.9,4.5,4.9,5.5,5.9,7.5]
    attrs = df_filtered["co2ccu_co2em"].unique() *100
    attrs = attrs.astype(int).astype(str)

    # Plotting each row as a bar with adjustable width
    bars = ax.bar(x_positions, df_filtered["fscp"] , width=widths, color= df_filtered["color_sector"], edgecolor='grey')


    for i, bar in enumerate(bars):
        if df_filtered.loc[i, 'sector'] == 'cement' and df_filtered.loc[i, 'type'] == 'ccu':
            if df_filtered.loc[i, 'fscp'] < cementccs_fscp:
                symbol = '✔'  # Green tick
                color = '#149821'
            else:
                symbol = '✘'  # Red cross
                color = '#E203D0'
                #ax.bar(bar.get_x()+ bar.get_width() / 2, bar.get_height(), bar.get_width(), color='white',alpha = 0.7, edgecolor='grey')
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    symbol, ha='center', va='bottom', fontsize=14, color=color)
        elif df_filtered.loc[i, 'sector'] == 'plane' and df_filtered.loc[i, 'type'] == 'ccu':
            if df_filtered.loc[i, 'fscp'] < aviationcomp_fscp:
                symbol = '✔'
                color = '#149821'
            else:
                symbol = '✘'
                color = '#E203D0'
                #ax.bar(bar.get_x()+ bar.get_width() / 2, bar.get_height(), bar.get_width(), color='white',alpha = 0.7, edgecolor='grey')
        # Place the symbol at the top of the bar
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    symbol, ha='center', va='bottom', fontsize=14, color=color)
        
    # Add a horizontal line at y=0
    ax.axhline(y=cementccs_fscp, xmin = 0.1, xmax = 0.7, color=color_dict["cement"], linewidth=1.5, linestyle='--', zorder = 0)
    ax.axhline(y=aviationcomp_fscp, xmin = 0.3, xmax = 0.9, color=color_dict["plane"], linewidth=1.5, linestyle='--', zorder = 0)

    #main legend
    ax.legend(handles=[Patch(facecolor=color_dict["cement"]), Patch(facecolor=color_dict["plane"])], edgecolor='grey', labels=['Cement (potential CO2 source)', "Aviation (potential CO2 utilisation)"], fontsize = 12, bbox_to_anchor=(0, 0.85),loc='lower left')
    
    #secondary legend

    na_patch = Line2D([0], [0], marker=r'$\checkmark$', color='w', label='CCU is the cheapest abatement\noption',
             markerfacecolor='#149821', markersize=10, markeredgewidth=0, markeredgecolor='#149821')
    fossil_patch = Line2D([0], [0], marker=r'$\times$', color='w', label='CCU more costly than alternative\noption (CCS or CDR compensation)',
             markerfacecolor='#E203D0', markersize=10, markeredgewidth=0, markeredgecolor='#E203D0')
    leg2 = fig.legend(handles=[na_patch,fossil_patch], bbox_to_anchor=(0.1, 0.68),loc='lower left', fontsize = 12)
    ax.add_artist(leg2)


    ax.text(3, -0.1, "CCU for cement and aviation,\nfor varying emission attributions\n(to the user sector)", ha='center', va='center', fontsize=12,transform=ax.get_xaxis_transform())
    # add delimiation line for cement ccs and aviation comp
    ax.set_xticks([0,1.7,2.7,3.7,4.7,5.7,7.5])
    ax.set_xticklabels(["CCS\n(cement)",attrs[0]+"%", attrs[1]+"%", attrs[2]+"%", attrs[3]+"%",attrs[4]+"%","CDR compensation\n(aviation)"])

    #axes size
    plt.setp(ax.get_yticklabels(), fontsize=12)
    plt.setp(ax.get_xticklabels(), fontsize=12)

    ax = change_spines(ax)
    ax.set_ylabel("Abatement cost (EUR/tCO2)", fontsize = 12)
    ax.set_title("Abatement cost for different CCU attributions", fontweight="bold",loc = "left")

    fig.tight_layout()
    fig.savefig('././figs/main_CementaviationCCUAttributin.png', format='png', dpi = 200)
    #plt.show()

def plot_large_panel(dfs):
    dfs = add_colors_units_rename(dfs)
    dfs = sort_data(dfs)

    #QUICKFIX: removing blueh2 from solution space for this supplementary figure
    dfs = dfs[dfs["type"] != "blueh2"]

    #set font size
    SMALL_SIZE = 15
    MEDIUM_SIZE = 17
    BIGGER_SIZE = 22

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE-1)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    plt.rc('axes', titlesize=BIGGER_SIZE)
    plt.rcParams['legend.title_fontsize'] = MEDIUM_SIZE

    ## First 3 rows: subplots
    fig, axes = plt.subplots(nrows = 3,ncols=5, figsize=(21,20))

    idx = 0
    for name, df in dfs.groupby("sector", sort = False):
        unit = df["unit"].iloc[0]
        color_sector = np.unique(df["color_sector"])[0]

        df = df.reset_index()
        
        axes[0,idx].bar(df["code"], df["lco_noh2co2"], color = df["color_type"], edgecolor = "slategrey")

        axes[0,idx].bar(df["code"], df["co2_cost"], bottom =df["lco_noh2co2"]  ,color = df["color_type"], alpha = 0.8, hatch = 'o', edgecolor = "slategrey", label = "co2")
        axes[0,idx].bar(df["code"], df["h2_cost"], bottom =df["lco_noh2co2"] +df["co2_cost"],color = df["color_type"], alpha = 0.8, hatch = '++', edgecolor = "slategrey", label = "h2")

        #look for nans (ie missing technologies)
        nan_idx = np.where(df['cost'].isnull())[0]
        axes[0,idx].bar(df["code"][nan_idx], np.nanmax(df["cost"])*1.05, facecolor='white',  hatch='/', edgecolor = "lightgrey")

        #make axes nicer
        axes[0,idx] = change_spines(axes[0,idx])
        #add a couple of parameters
        axes[0,idx].set_title(rename_sectors[name])#, backgroundcolor = color_sector , position=(0.5, 0.5))
        if idx == 0:
            axes[0,idx].set_ylabel(f"Levelized cost \n(EUR{unit})")
        else:
            axes[0,idx].set_ylabel(f"(EUR{unit})")
        axes[0,idx].set_ylim(0, np.nanmax(df["cost"])*1.05)


        #calculate max emissions and use to scale alpha of barplot
        max_em = np.nanmax(df["em"].to_numpy())
        ems_rel = [to_rgba('grey', alpha=np.abs(perc) / max_em) if perc > 0 else to_rgba('grey', alpha=0) for perc in df["em"].to_numpy()]
        
        #plot emissions
        #axes[1,idx].bar(df["code"], df["em"], color = [to_rgba('grey', alpha=np.abs(perc) / max_em) for perc in df["em"].to_numpy()], edgecolor = "grey")
        axes[1,idx].bar(df["code"], df["em"], color = ems_rel, edgecolor = "grey")
        axes[1,idx] = change_spines(axes[1,idx])

        #look for nans
        nan_idx = np.where(df['em'].isnull())[0]
        axes[1,idx].bar(df["code"][nan_idx], np.nanmax(df["em"])+10, facecolor='white', hatch='/', edgecolor = "lightgrey")
        axes[1,idx].bar(df["code"][nan_idx], -np.nanmax(df["em"]), facecolor='white', hatch='/', edgecolor = "lightgrey")
        axes[1,idx].axhline(0, color='black', lw = 0.75)
        
        # if idx == 0:
        #     axes[1,idx].set_ylabel(f"CO2 emissions \n (tCO2{unit})")
        if idx ==0:
            axes[1,idx].set_ylabel(f"CO2 emissions \n (tCO2{unit})")
        else:
            axes[1,idx].set_ylabel(f"(tCO2{unit})")
        axes[1,idx].set_ylim(-max_em*0.2, max_em*1.05)
        #axes[1,idx].tick_params(rotation=90)

        #share axis between line 1 & 2
        axes[1,idx].sharex(axes[0,idx])
        #extra line that goes toogether with sharex to remove the x labels for the first row
        plt.setp(axes[0,idx].get_xticklabels(), visible=False)

        #plot fscp
        #axes[2,idx].bar(df["code"], df["fscp"], color = df["color_sector"] ,edgecolor = "grey") 
        axes[2,idx].bar(df["code"], df["fscp"], color = df["color_type"] ,edgecolor = "grey")
        axes[2,idx] = change_spines(axes[2,idx])


        max_fscp = np.nanmax(dfs["fscp"].to_numpy())
        #look for nans (ie missing technologies)
        nan_idx = np.where(df['fscp'].isnull())[0]
        axes[2,idx].bar(df["code"][nan_idx], max_fscp * 1.3, facecolor='white', hatch='/', edgecolor = "lightgrey")
        #index = 0 corresponds to the fossil option
        axes[2,idx].bar(df["code"][0], max_fscp * 1.3, facecolor='white', hatch='/', edgecolor = "black")

        if idx == 0:
            axes[2,idx].set_ylabel(f"Abatement cost \n(EUR/tCO2)")  
        # axes[2,idx].set_ylim(0, np.nanmax(df["fscp"])*1.05)
        axes[2,idx].set_ylim(0, max_fscp * 1.05)
        #share axis between line 1 & 2
        axes[2,idx].sharex(axes[1,idx])
        
        # # Use this to share y axis
        # if idx > 0:
        #     axes[2,idx].sharey(axes[2,0])
        #     axes[2,idx].set_ylabel(None)
        axes[2,idx].tick_params(axis = "x",rotation=90)

        #extra line that goes toogether with sharex to remove the x labels for the first row
        plt.setp(axes[1,idx].get_xticklabels(), visible=False)
        
        #add annotations for the technologies that are missing, and remove the relevant x-ticks
        x_lab = axes[2,idx].get_xticklabels()
        x_tick = axes[2,idx].get_xticks()
        for x in nan_idx:
            if x != 0:
                axes[2,idx].annotate(df["code"][x], xy=(x-0.25, 25), xytext=(x-0.25, 25), rotation= 90, color = "grey", fontsize=MEDIUM_SIZE)
                axes[1,idx].annotate(df["code"][x], xy=(x-0.25, 0), xytext=(x-0.25, 0),va = "bottom", rotation= 90, color = "grey", fontsize = MEDIUM_SIZE)
                axes[0,idx].annotate(df["code"][x], xy=(x-0.25, 0), xytext=(x-0.25, 0),va = "bottom", rotation= 90, color = "grey", fontsize = MEDIUM_SIZE)
                x_lab[x] = ""
        axes[2,idx].set_xticks(x_tick)
        axes[2,idx].set_xticklabels(x_lab)

        #step to next iteration
        idx += 1


    #colorbar function
    colors_tech = {k: color_dict_tech[k] for k in ('h2', 'efuel', 'comp', 'ccu', 'ccs')}
    cmap = ListedColormap(colors_tech.values())

    fig.subplots_adjust(right=0.87)
    cbar_ax = fig.add_axes([0.92, 0.1, 0.02, 0.5])

    colbar = fig.colorbar(ScalarMappable( cmap=cmap), cax = cbar_ax)

    colbar.set_ticks([0.1, 0.3, 0.5, 0.7, 0.9])
    colbar.set_ticklabels(['H2/NH3', 'E-fuel','Compen-\nsation', 'CCU', 'CCS'])


    h2_patch = Patch(facecolor='white', edgecolor='slategrey', label='Low-emission H2', hatch='+++')
    #co2ts_patch = Patch(facecolor='white', edgecolor='grey', label='CO2 transport\n and storage',hatch ='////')
    co2_patch = Patch(facecolor='white', edgecolor='slategrey', label='Non-fossil CO2',hatch ='o')
    fig.legend(handles=[h2_patch,co2_patch], title = "Cost contributions",bbox_to_anchor=(0.52, 0.4, 0.49, 0.5), fontsize = MEDIUM_SIZE)
    
    na_patch = Patch(facecolor='white', edgecolor='grey', label='No option\navailable',hatch ='//')
    fossil_patch = Patch(facecolor='white', edgecolor='k', label='Fossil\nreference',hatch ='//')
    leg2 = fig.legend(handles=[na_patch,fossil_patch],bbox_to_anchor=(0.5, 0.32, 0.49, 0.5), fontsize = MEDIUM_SIZE)
    fig.add_artist(leg2)

    ### PLOT FULL FIGURE ###
    h2_LCO = dfs["h2_LCO"].unique()[0]
    co2_LCO = dfs["co2_LCO"].unique()[0]
    fig.suptitle(f"Abatement cost for the HTE sectors, based on optimistic parameter projection for 2050.\nCost of low-emission H2: {h2_LCO} EUR/MWh, cost of non-fossil CO2: {co2_LCO:.0f} EUR/tCO2.", fontsize = BIGGER_SIZE)
    #fig.tight_layout()
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.45, hspace=0.1)
    #fig.savefig('./././myimage.png', format='png', dpi=600, bbox_inches='tight')
    fig.savefig('././figs/supp_FSCPcalcbreakdown.png', format='png', dpi = 300, bbox_inches='tight')
    #plt.show()

def plot_barplotfscp(dfs, dfs_breakdown, dfs_steelccs, sector = "steel", type = "h2",sensitivity = "h2_LCO"):
    dfs = add_colors_units_rename(dfs)
    dfs_breakdown[["type", "sector"]] = dfs_breakdown["tech"].str.split("_", expand=True)

    #filter df to get relevant LCOs
    sub_df_LCO = dfs[(dfs["sector"]==sector) & ((dfs["type"]==type) | (dfs["type"]=="fossil") | (dfs["type"]=="ccs") )]
    sub_df_LCO_breakdown = dfs_breakdown[(dfs_breakdown["sector"]==sector) & ((dfs_breakdown["type"]==type) | (dfs_breakdown["type"]=="fossil") | (dfs_breakdown["type"]=="ccs") )]
    
    #filter steel ccs sensitivity df to get the relevant row
    sub_df_steelccslow = dfs_steelccs[0][(dfs_steelccs[0]["sector"]==sector) & (dfs_steelccs[0]["type"]=="ccs") & (dfs_steelccs[0]["ccs_steel_capex"] == 782.5)]
    sub_df_steelccshigh = dfs_steelccs[1].loc[(dfs_steelccs[1]["sector"]==sector) & (dfs_steelccs[1]["type"]=="ccs") & (dfs_steelccs[1]["ccs_steel_capex"] == 978.7)]
    # error here are the +/- value.
    steelccs_lco_error = (sub_df_steelccshigh["cost"].values[0] - sub_df_steelccslow["cost"].values[0])/2
    steelccs_fscp_error = (sub_df_steelccshigh["fscp"].values[0] - sub_df_steelccslow["fscp"].values[0])/2

    #filter df to get relevant FSCP
    sub_df_FSCP = dfs[(dfs["sector"]==sector) & (dfs["type"]==type) ]
    sub_df_FSCP2 = dfs[(dfs["sector"]==sector) & (dfs["type"]=="ccs") ]


    unit = np.unique(sub_df_LCO["unit"])[0]
    fscp_color = np.unique(sub_df_FSCP["color_type"])[0]
    fscp_color2 = np.unique(sub_df_FSCP2["color_type"])[0]
    
    #following line is a bit hacky, will make code break if comparing options with the same cost (eg DRI when choosing DAC Co2 sensitivity)
    sub_df_LCO.drop_duplicates( "cost", inplace=True)
    sub_df_LCO.reset_index(inplace=True, drop = True)
    sub_df_LCO.drop(["elec"], axis = 1, inplace = True)
    sub_df_LCO = sub_df_LCO.round(2)
    
    #more hacky stuff for the steel LCO breakdown in particular
    sub_df_LCO_breakdown = sub_df_LCO_breakdown.drop_duplicates("LCO").dropna(axis=1, how='all').reset_index(drop = True)
    sub_df_LCO_breakdown = (sub_df_LCO_breakdown.apply(pd.to_numeric, errors="coerce").round(2).fillna(sub_df_LCO_breakdown)) #make sure all columns with numbers are numeric
    sub_df_LCO_breakdown.rename(columns = {"LCO": "cost"}, inplace = True)
    sub_df_LCO_breakdown.drop(["type", "sector", "tech"], axis =1, inplace = True)
    sub_df_LCO_breakdown = sub_df_LCO_breakdown[[ "cost", "capex", "opex", "other costs","ironore","scrap", "elec","fossilng", "h2", "fossilccoal", "fossilpci", "co2 transport and storage"]]
    
    #merge to make final df
    sub_df_LCO_merge = sub_df_LCO.merge(sub_df_LCO_breakdown,how ="left",  on =[ "cost"],validate = "1:1")
    
    # sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "ccs"), "code"] = sub_df_LCO["code"] + ",\nH2 cost =\n" +sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh"
    sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "ccs"), "code"] = sub_df_LCO["h2_LCO"].astype(str) + " \nEUR/MWh"

    #sort so the fossil pathway is first
    sub_df_LCO.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)
    sub_df_LCO_merge.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)

    fig, axes = plt.subplots(nrows = 2,ncols=1, figsize=(14,14))

    #set font size
    SMALL_SIZE = 15
    MEDIUM_SIZE = 17
    BIGGER_SIZE = 19

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    plt.rc('axes', titlesize=BIGGER_SIZE)


    x_pos = [0,3,6,7.5,9,10.5]
    height = 0
    alpha_list = [0.8, 0.7, 0.6, 0.5,0.4, 0.3, 0.2, 0.1, 0, 0.2, 0.5]
    color = ["white", "white", "white", "white", "white", "white","white","white","white", "darkgrey","darkgrey"]
    labels = {"capex":"CAPEX", "opex":"O&M", "other costs":"other OPEX", "ironore":"Iron ore", "scrap":"Scrap,\nferroalloys","elec":"Electricity","fossilng": "Natural gas", "h2":"H2", "fossilccoal":"Coking coal", "fossilpci":"PCI coal","co2 transport and storage": "CO2 transport\n& storage"}

    #first, plot colorerd layer
    axes[0].bar(x_pos, sub_df_LCO_merge["cost"], color = sub_df_LCO_merge["color_type"],  edgecolor = "grey")

    #then, transparent stacked bars
    for i, comp in enumerate(["capex","opex", "other costs","ironore","scrap", "elec", "fossilng", "h2", "fossilccoal", "fossilpci", "co2 transport and storage"]):
        with pd.option_context("future.no_silent_downcasting", True):
            column = sub_df_LCO_merge[comp].fillna(0).infer_objects(copy=False)
        axes[0].bar(x_pos, column, bottom = height, edgecolor = "dimgrey", color = color[i], alpha = alpha_list[i])

        annot_height = height + column/2
        height += column
        
        #here, add any annotation needed
        if column[0] > 0:
            axes[0].hlines(annot_height[0], 0.4, 0.55, colors = "darkgrey", linewidth = 1)
            if comp != "scrap":
                axes[0].text(x=0.6,y= annot_height[0], s=labels[comp], verticalalignment='center', c= "grey")
            else:
                axes[0].text(x=0.6, y= annot_height[0]-30, s=labels[comp], verticalalignment='center', c= "grey")

        if column[1] > 0:
            if comp != "scrap":
                if comp != "co2 transport and storage":
                    axes[0].text(x=3.6,y= annot_height[1], s=labels[comp], verticalalignment='center', c= "grey")
                    axes[0].hlines(annot_height[1], 3.4, 3.55, colors = "darkgrey", linewidth = 1)
                else:
                    axes[0].annotate(labels[comp],(3.4, annot_height[1]), xytext = (3.6, annot_height[1]+20),c= "grey",
                                     arrowprops=dict(color='darkgrey', width = 0.05, headwidth = 0))
                    #texts.append(axes[0].text(x=3.6,y= annot_height[2]+20, s=labels[comp]))
            else:
                axes[0].text(x=3.6,y= annot_height[1]-25, s=labels[comp], verticalalignment='center', c= "grey")
                axes[0].hlines(annot_height[1], 3.4, 3.55, colors = "darkgrey", linewidth = 1)

        if column[5] > 0:
            axes[0].hlines(annot_height[5], 10.9, 11.05, colors = "darkgrey", linewidth = 1)
            if comp != "scrap" and comp != "fossilng":
                axes[0].text(x=11.1,y= annot_height[5], s=labels[comp], verticalalignment='center', c= "grey")
            elif comp == "scrap":
                axes[0].text(x=11.1,y= annot_height[5]-25, s=labels[comp], verticalalignment='center', c= "grey")
            else:
                axes[0].text(x=11.1,y= annot_height[5]+20, s=labels[comp], verticalalignment='center', c= "grey")
        
    #add errorbars to CCS bar
    e = axes[0].errorbar(x_pos[1], height[1], yerr = steelccs_lco_error, fmt = "none", color = "black", capsize = 5, capthick = 1)

    # axes[0].annotate('', xy=(5.2, -100),xytext=(11.2,-100),       
    #             arrowprops=dict(arrowstyle='-',facecolor='black', linestyle = "--"),
    #             annotation_clip=False)
    axes[0].legend([e], ["BF-BOF carbon capture CAPEX cost uncertainty\n"+r"($\pm$ 50% of base assumption)"], loc = "upper left")
    axes[0].annotate('H2-DRI-EAF, for different H2 costs',xy=(8.25,-100),xytext=(8.25,-100), color = "black", horizontalalignment = "center",
                annotation_clip=False, fontsize = MEDIUM_SIZE)

    #other plot settings
    axes[0].set_xticks(x_pos, sub_df_LCO_merge["code"])
    
    axes[0] = change_spines(axes[0])
    
    axes[0].set_title("Levelized cost comparison based on different H2 cost assumptions", fontweight="bold",loc = "left")
    axes[0].set_ylabel(f"Levelized cost \n(EUR{unit})", fontsize = MEDIUM_SIZE)



    #now, FSCP figure

    #calc best fit linear
    
    #find line of best fit
    a, b = np.polyfit(sub_df_FSCP["h2_LCO"], sub_df_FSCP["fscp"], 1)
    a2, b2 = np.polyfit(sub_df_FSCP2["h2_LCO"], sub_df_FSCP2["fscp"], 1)
    intersection = (b2-b)/(a-a2)

    s1 = axes[1].scatter(sub_df_FSCP["h2_LCO"], sub_df_FSCP["fscp"], c=sub_df_FSCP["color_type"], edgecolor = "grey", zorder =2)
    l1, = axes[1].plot(np.linspace(0,250), a*np.linspace(0,250) + b, c = fscp_color, alpha = 1, zorder = 1)


    s2 = axes[1].scatter(sub_df_FSCP2["h2_LCO"], sub_df_FSCP2["fscp"], c=sub_df_FSCP2["color_type"], edgecolor = "grey", zorder = 1)
    l2, = axes[1].plot(np.linspace(0,250), a2*np.linspace(0,250) + b2, c = fscp_color2, alpha = 1, zorder = 0)
    
    #add errorbars to CCS bar for fscp
    axes[1].fill_between([0,250], sub_df_FSCP2["fscp"].unique()[0]-steelccs_fscp_error, sub_df_FSCP2["fscp"].unique()[0]+steelccs_fscp_error, color = fscp_color2, alpha = 0.1)
    sh1, = axes[1].fill(np.NaN, np.NaN, fscp_color2, alpha=0.1)

    ## extra vline on bottom pannel at intersection- not sure if needed
    axes[1].vlines(intersection, 0,250,ls="--", color = "darkgrey", lw = 1)
    #dummy line for legend
    l3 = Line2D([0], [0], color='darkgrey', linewidth=1, linestyle='--')
    # Get current xticks and xticklabels
    xticks = list(axes[1].get_xticks())
    xticklabels = list(axes[1].get_xticklabels())

    # Add intersection to xticks and its label to xticklabels
    xticks.append(intersection)
    xticklabels.append(f'{intersection:.0f}')

    # Set new xticks and xticklabels
    axes[1].set_xticks(xticks)
    axes[1].set_xticklabels(xticklabels)

    # Change color of last tick label to grey
    for label in axes[1].get_xticklabels():
        if f'{intersection:.0f}' == label.get_text(): 
            label.set_color('darkgrey')

    ## extra annotations on bottom pannel- not sure if needed
    # axes[1].text(80,175, "DRI-EAF is the\ncheapest mitigation option", color = "grey", horizontalalignment="center",
    #              bbox=dict(facecolor = "white",edgecolor = "darkgrey", boxstyle="round,pad=0.5"))
    # axes[1].text(147,175, "BF-BOF-CCS is the\ncheapest mitigation option", color = "grey",horizontalalignment="center",
    #              bbox=dict(facecolor = "white",edgecolor = "darkgrey", boxstyle="round,pad=0.5"))

    axes[1] = change_spines(axes[1])
    
    axes[1].set_title("FSCP dependency on assumed H2 cost", fontweight="bold", loc ="left")
    axes[1].set_ylabel(f"Fuel-switching CO2 price \n(EUR/tCO2)", fontsize = MEDIUM_SIZE)
    axes[1].set_xlabel(f"Hydrogen cost (EUR/MWh)", fontsize = MEDIUM_SIZE)
    axes[1].set_ylim(0, 255)
    axes[1].set_xlim(0, 255)
    # axes[1].legend([(s1,l1), (s2,l2)],["DRI-EAF replacing BF-BOF steel","BF-BOF-CCS replacing BF-BOF steel"], loc = "lower right")
    axes[1].legend([(s1,l1), (s2,l2,sh1), (l3)],
        ["H2-DRI-EAF replacing BF-BOF steel",
        "BF-BOF-CCS replacing BF-BOF steel, ribbon indicating\n"+ r"$\pm$ 50% cost uncertainty on BF-BOF carbon capture CAPEX", 
        "H2 cost at which BF-BOF-CCS and H2-DRI-EAF\nhave the same abatement cost (central assumption)",
        ]	
    )#loc = "lower right")

    #axes size
    plt.setp(axes[0].get_yticklabels(), fontsize=MEDIUM_SIZE)
    plt.setp(axes[0].get_xticklabels(), fontsize=MEDIUM_SIZE)
    plt.setp(axes[1].get_yticklabels(), fontsize=MEDIUM_SIZE)
    plt.setp(axes[1].get_xticklabels(), fontsize=MEDIUM_SIZE)

    #add panel letter
    for n, ax in enumerate(axes):   
        ax.text(-0.1, 1.05, string.ascii_lowercase[n], transform=ax.transAxes, 
                size=18, weight='bold')

    fig.tight_layout()
    #plt.show()
    #fig.savefig('./././myimage.png', format='png', dpi=600, bbox_inches='tight')
    fig.savefig('././figs/main_steelLCObreakdown.png', format='png', dpi = 200)

def curly(x,y, scale, ax=None):
    if not ax: ax=plt.gca()
    tp = TextPath((0, 0), "}", size=1)
    trans = mtrans.Affine2D().scale(1, scale) + \
        mtrans.Affine2D().translate(x,y) + ax.transData
    pp = PathPatch(tp, lw=0, fc="k", transform=trans)
    ax.add_artist(pp)

def plot_barplotaviation(dfs, dfs_breakdown, h2costs,co2ts_costs, sector = "plane", type = "efuel",sensitivity = "h2_LCO"):
    dfs = add_colors_units_rename(dfs)
    dfs_breakdown[["type", "sector"]] = dfs_breakdown["tech"].str.split("_", expand=True)

    #filter df to get relevant LCOs
    sub_df_LCO = dfs[(dfs["sector"]==sector) & ((dfs["type"]==type) | (dfs["type"]=="fossil") | (dfs["type"]=="comp") )]
    sub_df_LCO_breakdown = dfs_breakdown[(dfs_breakdown["sector"]==sector) & ((dfs_breakdown["type"]==type) | (dfs_breakdown["type"]=="fossil") | (dfs_breakdown["type"]=="comp") )]

    unit = np.unique(sub_df_LCO["unit"])[0]
    
    #following line is a bit hacky, will make code break if comparing options with the same cost (eg DRI when choosing DAC Co2 sensitivity)
    sub_df_LCO.drop_duplicates( "cost", inplace=True)
    sub_df_LCO.reset_index(inplace=True, drop = True)
    sub_df_LCO.drop(["elec"], axis = 1, inplace = True)
    sub_df_LCO = sub_df_LCO.round(5)
    
    #more hacky stuff for the steel LCO breakdown in particular
    sub_df_LCO_breakdown = sub_df_LCO_breakdown.drop_duplicates("LCO").dropna(axis=1, how='all').reset_index(drop = True)
    sub_df_LCO_breakdown = (sub_df_LCO_breakdown.apply(pd.to_numeric, errors="coerce").round(5).fillna(sub_df_LCO_breakdown))
    sub_df_LCO_breakdown.rename(columns = {"LCO": "cost"}, inplace = True)
    sub_df_LCO_breakdown.drop(["type", "sector", "tech"], axis =1, inplace = True)

    sub_df_LCO_breakdown["compco2"] = sub_df_LCO_breakdown["co2"]

    with pd.option_context("future.no_silent_downcasting", True):
        MtJ_ch3oh_h2_costs = sub_df_LCO_breakdown["MtJ_ch3oh_h2"].dropna().diff().fillna(0).infer_objects(copy=False)
        comp_co2ts_costs = sub_df_LCO_breakdown["co2 transport and storage"].dropna().diff().fillna(0).infer_objects(copy=False)
    
    sub_df_LCO_breakdown = sub_df_LCO_breakdown[[ "cost", "other costs","MtJ_capex", "MtJ_opex","MtJ_elec","MtJ_h2","MtJ_co2", "MtJ_ch3oh_capex","MtJ_ch3oh_co2","MtJ_ch3oh_elec","MtJ_ch3oh_h2","MtJ_ch3oh_opex","compco2","co2 transport and storage","fossilJ"]]

    #merge to make final df
    sub_df_LCO_merge = sub_df_LCO.merge(sub_df_LCO_breakdown,how ="left",  on =[ "cost"],validate = "1:1")

    # sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "comp"), "code"] = sub_df_LCO["code"] + ",\nH2 cost =\n" +sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh"
    sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "comp"), "code"] = "E-fuel"#sub_df_LCO["h2_LCO"].astype(str) + " \nEUR/MWh"

    #sort so the fossil pathway is first
    sub_df_LCO.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)
    sub_df_LCO_merge.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)

    fig, axes = plt.subplots(nrows = 1,ncols=1, figsize=(19,20))

    #set font size
    SMALLEST_SIZE = 17
    SMALL_SIZE = 20
    MEDIUM_SIZE = 22
    BIGGER_SIZE = 24

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    plt.rc('axes', titlesize=BIGGER_SIZE)


    #x_pos = [0,3,6,7.5,9,10.5]
    x_pos = [0,4,10]
    height = 0
    alpha_list = [0.8, 0.6, 0.4, 0.2,0.3, 0.5, 0.7, 0.9, 0.4, 0.2,0.5, 0.8]
    color = ["white", "white", "white", "white", "white", "white","white","white","white", "darkgrey","darkgrey","white"]
    labels = {"MtJ_capex":"CAPEX: MtJ", "MtJ_opex":"O&M: MtJ","MtJ_elec":"Electricity: MtJ ","MtJ_h2":"Hydrogen: MtJ ","MtJ_co2":"CO2 losses: MtJ", "other costs":"Aircraft cost and\noperating fees", "MtJ_ch3oh_capex":"CAPEX: Methanol synthesis","MtJ_ch3oh_co2":"CO2: Methanol synthesis",
            "MtJ_ch3oh_elec":"Electricity: Methanol synthesis","MtJ_ch3oh_h2":"Hydrogen: Methanol synthesis","MtJ_ch3oh_opex":"O&M: Methanol synthesis",
            "compco2":"CO2: CDR ","elec":"Electricity","fossilJ":"Fossil jet fuel","co2 transport and storage": "CO2 transport\n& storage", "MtJ_allopex":"All OPEX: MtJ"}
    

    sub_df_LCO_merge["MtJ_allopex"] = sub_df_LCO_merge["MtJ_opex"] + sub_df_LCO_merge["MtJ_elec"] + sub_df_LCO_merge["MtJ_h2"]

    #small change to total cost of efuel option: we account for uncertainty in the cost of H2.
    # this means adding the costs of different h2 assumptions to make the main bar bigger.
    # sub_df_LCO_merge.loc[2, "cost"] = sub_df_LCO_merge.loc[2, "cost"] + MtJ_ch3oh_h2_costs.sum()
    
    #first, plot colorerd layer
    axes.bar(x_pos, sub_df_LCO_merge["cost"], color = sub_df_LCO_merge["color_type"],  edgecolor = "grey")
    j=0
    #then, transparent stacked bars
    for i, comp in enumerate(["other costs","compco2","MtJ_ch3oh_co2","MtJ_co2","MtJ_capex","MtJ_ch3oh_capex", "MtJ_allopex", "MtJ_ch3oh_opex","MtJ_ch3oh_elec","MtJ_ch3oh_h2","fossilJ","co2 transport and storage"]):
        with pd.option_context("future.no_silent_downcasting", True):
            column = sub_df_LCO_merge[comp].fillna(0).infer_objects(copy=False)
        #find h2 cost for MtJ
        if comp == "MtJ_ch3oh_h2":
            bars = axes.bar(x_pos, column, bottom = height, edgecolor = None, color = color[i], alpha = alpha_list[i])
            #axes.text(x = x_pos[2]- 1.5, y= height[2] + column[2], s="Hydrogen cost:\n"+str(h2costs[0])+"EUR/MWh", verticalalignment='center', c= "darkgrey", fontsize = 12)

            annot_height = height + column/2
            height += column
            temp_height = height[2]
            for j, val in enumerate(MtJ_ch3oh_h2_costs):
                if j != 0:
                    axes.bar(x_pos[2]+j*0.8, val, bottom = temp_height, edgecolor = None, color = color_dict_tech["efuel"])
                    axes.bar(x_pos[2]+j*0.8, val, bottom = temp_height, edgecolor = "black", color = color[i], alpha = alpha_list[i])#,linestyle="--", lw =1)
                else:
                    pass
                axes.text(x = x_pos[2]- 0.5+j*0.8, y= temp_height-column[2]/2+val, s=str(h2costs[j])+"\nEUR/MWh", verticalalignment='center',horizontalalignment = "right", c= "darkgrey", fontsize = SMALLEST_SIZE)
                temp_height += val
                
        elif comp == "co2 transport and storage":
            bars = axes.bar(x_pos, column, bottom = height, edgecolor = None, color = color[i], alpha = alpha_list[i])

            annot_height = height + column/2
            height += column
            temp_height = height[1]
            for k, val in enumerate(comp_co2ts_costs):
                if k != 0:
                    axes.bar(x_pos[1]+k*0.8, val, bottom = temp_height, edgecolor = None, color = color_dict_tech["comp"])
                    axes.bar(x_pos[1]+k*0.8, val, bottom = temp_height, edgecolor = "grey", color = color[i], alpha = alpha_list[i])#,linestyle="--", lw =1)
                else:
                    pass
                axes.text(x = x_pos[1]- 1+k*0.8, y= temp_height-column[1]/2+val+((k-1)*0.0015), s=str(co2ts_costs[k])+"\nEUR/tCO2", verticalalignment='center',horizontalalignment = "center", c= "darkgrey", fontsize =SMALLEST_SIZE)
                temp_height += val
        else:
            bars = axes.bar(x_pos, column, bottom = height, edgecolor = None, color = color[i], alpha = alpha_list[i])
            annot_height = height + column/2
            height += column
            
        
        #here, add any annotation needed
        if column[0] > 0:
            axes.hlines(annot_height[0], 0.4, 0.55, colors = "darkgrey", linewidth = 1)
            if comp != "scrap":
                axes.text(x=0.6,y= annot_height[0], s=labels[comp], verticalalignment='center', c= "dimgrey", fontsize = SMALL_SIZE)
            else:
                axes.text(x=0.6, y= annot_height[0], s=labels[comp], verticalalignment='center', c= "dimgrey", fontsize = SMALL_SIZE)

        if column[1] > 0:
            if comp =="co2 transport and storage":
                axes.text(x = x_pos[1]-3.5, y = height[1]+0.005, s= "CO2 transport and\nstorage costs for:",verticalalignment='center', c= "dimgrey", zorder=2, fontsize = SMALL_SIZE)
                #axes.hlines(annot_height[1], x_pos[1]+0.4, x_pos[1]+0.55, colors = "darkgrey", linewidth = 1, zorder=2)
            else:
                axes.text(x= x_pos[1]+0.6,y= annot_height[1], s=labels[comp], verticalalignment='center', c= "dimgrey", zorder=2, fontsize = SMALL_SIZE)
                axes.hlines(annot_height[1], x_pos[1]+0.4, x_pos[1]+0.55, colors = "darkgrey", linewidth = 1, zorder=2)

        if column[2] > 0:
            if comp not in ["MtJ_allopex", "MtJ_ch3oh_capex","MtJ_ch3oh_opex","MtJ_ch3oh_elec","MtJ_ch3oh_h2"]:
                axes.text(x=x_pos[2]+0.6,y= annot_height[2], s=labels[comp], verticalalignment='center', c= "dimgrey", zorder=2, fontsize = SMALL_SIZE)
                axes.hlines(annot_height[2], x_pos[2]+0.4, x_pos[2]+0.55, colors = "darkgrey", linewidth = 1, zorder=2)

            elif comp in ["MtJ_allopex", "MtJ_ch3oh_capex","MtJ_ch3oh_opex","MtJ_ch3oh_elec"]:
                axes.annotate(labels[comp],(x_pos[2]+0.4, annot_height[2]), xytext = (x_pos[2]+0.55, annot_height[2]+0.0009+j*0.0022),c= "dimgrey",
                                      arrowprops=dict(color='darkgrey', width = 0.05, headwidth = 0), zorder=2, fontsize = SMALL_SIZE)
                j+=1
 
            else: #case of hydrogen for methanol synthesis
                axes.text(x=x_pos[2]-3.9,y= height[2]+0.009, s="Hydrogen cost\nin e-jet fuel\nfor different LCOH",
                           verticalalignment='center', c= "dimgrey", fontsize = SMALL_SIZE)
                


        # Find the index of "MtJ_co2"
        if comp == "MtJ_co2":
            mtj_co2_bottom = height - column  # This is the bottom position of the "MtJ_co2" section
            mtj_co2_height = column  # This is the height of the "MtJ_co2" section

            # # Draw a grey rectangle highlighting "MtJ_co2"
            # rect = Rectangle(
            #     (bars[1].get_x() - bars[0].get_width() * 0.1, 0),  # x, y position (left edge of the rectangle)
            #     (bars[2].get_x()-bars[1].get_x()) * 1.9 ,  # width spans all bars + some padding
            #     mtj_co2_bottom[2]+mtj_co2_height[2],  # height
            #     fc=(0.7,0.7,0.7,0.2), ec=(0,0,0,0.7), zorder=1  # semi-transparent grey rectangle
            # )
            # axes.add_patch(rect)

            # Draw a dashed line at the top of the "MtJ_co2" section
            axes.axhline(y=mtj_co2_bottom[2]+mtj_co2_height[2], xmin = 0.34, xmax = 1.08,
                         color='black', linestyle='--', linewidth=1.5, label='common costs', clip_on=False)

            # Add label "common costs" on the rightmost edge of the rectangle
            axes.text(
                bars[-1].get_x() + bars[-1].get_width() +3.5,
                mtj_co2_bottom[0] + mtj_co2_height[0] / 2,  # position y (center of the rectangle)
                'CDR and e-fuels:\ncommon costs', 
                va='center', ha='left', fontsize=MEDIUM_SIZE, color='black',
                clip_on=False
            )
            #add cost differenece
            axes.text(
                bars[-1].get_x() + bars[-1].get_width() +3.5, 
                mtj_co2_bottom[0] *2,  
                'CDR and e-fuels:\ncost differences', 
                va='center', ha='left', fontsize=MEDIUM_SIZE, color='black'
            )

    #other plot settings
    axes.set_xticks(x_pos, sub_df_LCO_merge["code"])
    
    axes = change_spines(axes)
    
    axes.set_title("Aviation: Levelized cost comparison between CDR compensation and e-fuels", fontweight="bold",loc = "left", fontsize = BIGGER_SIZE)
    axes.set_ylabel(f"Levelized cost (EUR{unit})", fontsize = MEDIUM_SIZE+1)

    #axes size
    plt.setp(axes.get_yticklabels(), fontsize=MEDIUM_SIZE)
    plt.setp(axes.get_xticklabels(), fontsize=MEDIUM_SIZE)


    #fig.tight_layout()
    fig.savefig('././figs/main_aviationCDRefuels.png', format='png', dpi = 200,bbox_inches='tight')
    #plt.show()

def plot_barplotfuels(dfs, dfs_breakdown, sector = "steel", type = "h2",sensitivity = "h2_LCO"):
    dfs = add_colors_units_rename(dfs)
    #techs being compared: "MtJ" and "fossilJ"
    
    unit = "/MWh"
    
    #filter df to get relevant LCOs
    sub_df_LCO = dfs[(dfs["tech"]=="MtJ") | (dfs["tech"]=="fossilJ")]
    
    sub_df_LCO_breakdown = dfs_breakdown[(dfs_breakdown["tech"]=="MtJ") | (dfs_breakdown["tech"]=="fossilJ")]
    
    #following line is a bit hacky, will make code break if comparing options with the same cost (eg DRI when choosing DAC Co2 sensitivity)
    sub_df_LCO.drop_duplicates( "cost", inplace=True)
    sub_df_LCO.reset_index(inplace=True, drop = True)
    sub_df_LCO.drop(["elec"], axis = 1, inplace = True)
    sub_df_LCO = sub_df_LCO.round(2)

    #more hacky stuff for the steel LCO breakdown in particular
    sub_df_LCO_breakdown = sub_df_LCO_breakdown.drop_duplicates("LCO").dropna(axis=1, how='all').reset_index(drop = True)
    sub_df_LCO_breakdown = (sub_df_LCO_breakdown.apply(pd.to_numeric, errors="coerce").round(2).fillna(sub_df_LCO_breakdown))
    sub_df_LCO_breakdown.rename(columns = {"LCO": "cost"}, inplace = True)
    sub_df_LCO_breakdown.drop(["tech"], axis =1, inplace = True)
    selected_comps = [ "cost", "capex","ch3oh_capex", "opex", "ch3oh_opex","elec","ch3oh_elec", "h2","ch3oh_h2","ch3oh_co2" ]
    sub_df_LCO_breakdown = sub_df_LCO_breakdown[selected_comps]
    
    #merge to make final df
    sub_df_LCO_merge = sub_df_LCO.merge(sub_df_LCO_breakdown,how ="left",  on =[ "cost"],validate = "1:1")
    
    # sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "ccs"), "code"] = sub_df_LCO["code"] + ",\nH2 cost =\n" +sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh"
    sub_df_LCO_merge.loc[(sub_df_LCO["tech"] != "fossilJ"), "code"] = "H2 : "+sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh,\nCO2 : "+sub_df_LCO["co2_LCO"].astype(str) + " EUR/tCO2"

    #sort so the fossil pathway is first
    sub_df_LCO.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)
    sub_df_LCO_merge.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)
    sub_df_LCO_merge["color_type"] = ["#31393C","#8c6570", "#8c6570", "#8c6570", "#8c6570" ]

    # color_dict = {"cement":"#EABE7C", "steel":"#8c6570","ship":"#0471A6","plane":"#61E8E1", "chem":"#AFB3F7"}
    # color_dict_tech = {"fossil":"#31393C",

    fig, axes = plt.subplots(nrows = 1,ncols=1, figsize=(14,10))

    x_pos = [2,4,6,8,10]

    height = 0
    alpha_list = [ 0.6, 0.5, 0.4, 0.3, 0.3,0.4, 0.5, 0.2, 0.1,0]
    color = ["white", "white", "white", "white", "darkgrey","darkgrey", "darkgrey","white", "white","white"]
    labels = {"capex":"CAPEX (methanol-to-jetfuel)","ch3oh_capex":"CAPEX (h2-to-methanol)", "opex":"OPEX (methanol-to-jetfuel)","ch3oh_opex":"OPEX (h2-to-methanol)",
                "elec":"Electricity (methanol-to-jetfuel)","ch3oh_elec":"Electricity (h2-to-methanol)","ch3oh_heat":"Heat (h2-to-methanol)",
                  "h2":"Green H2 (methanol-to-jetfuel)", "ch3oh_h2":"Green H2 (h2-to-methanol)", "ch3oh_co2":"DAC CO2 (h2-to-methanol)"}

    #first, plot colorerd layer
    axes.bar(x_pos, sub_df_LCO_merge["cost"], color = sub_df_LCO_merge["color_type"],  edgecolor = "grey")

    #then, transparent stacked bars
    for i, comp in enumerate(selected_comps[1:]):
        with pd.option_context("future.no_silent_downcasting", True):
            column = sub_df_LCO_merge[comp].fillna(0).infer_objects(copy=False)

        axes.bar(x_pos, column, bottom = height, edgecolor = "dimgrey", color = color[i], alpha = alpha_list[i])

        annot_height = height + column/2
        height += column
        
        #here, add any annotation needed
        if column[0] > 0:
            axes.hlines(annot_height[0], 0.4, 0.55, colors = "darkgrey", linewidth = 1)
            if comp != "elec":
                axes.text(x=0.6,y= annot_height[0], s=labels[comp], verticalalignment='center', c= "grey")
            else:
                axes.text(x=0.6, y= annot_height[0]-20, s=labels[comp], verticalalignment='center', c= "grey")

        if column[4] > 0:
            
            if comp in ["capex","ch3oh_h2","ch3oh_co2"]:
                axes.text(x=10.6,y= annot_height[4], s=labels[comp], verticalalignment='center', c= "grey")
                axes.hlines(annot_height[4], 10.4, 10.55, colors = "darkgrey", linewidth = 1)
            else:
                axes.annotate(labels[comp],(10.4, annot_height[4]), xytext = (10.55, annot_height[4]+15*i),c= "grey",
                                      arrowprops=dict(color='darkgrey', width = 0.05, headwidth = 0))
                # axes.text(x=11.1,y= annot_height[4]+15*i, s=labels[comp], verticalalignment='center', c= "grey")
        
    #add annotation to xaxis

    # axes.annotate('', xy=(5.2, -100),xytext=(11.2,-100),       
    #             arrowprops=dict(arrowstyle='-',facecolor='black', linestyle = "--"),
    #             annotation_clip=False)

    axes.annotate('E-jet fuel, for different H2 and CO2 costs',xy=(6.8,-80),xytext=(6.8,-60), color = "black", horizontalalignment = "center",
                annotation_clip=False)

    #other plot settings
    axes.set_xticks(x_pos, sub_df_LCO_merge["code"], fontsize = 10)
    
    axes = change_spines(axes)
    
    axes.set_title("Levelized cost comparison based on different H2 cost assumptions", fontweight="bold",loc = "left")
    axes.set_ylabel(f"Levelized cost \n(EUR{unit})")



    # #now, FSCP figure

    # #calc best fit linear
    
    # #find line of best fit
    # a, b = np.polyfit(sub_df_FSCP["h2_LCO"], sub_df_FSCP["fscp"], 1)
    # a2, b2 = np.polyfit(sub_df_FSCP2["h2_LCO"], sub_df_FSCP2["fscp"], 1)
    # intersection = (b2-b)/(a-a2)

    # s1 = axes[1].scatter(sub_df_FSCP["h2_LCO"], sub_df_FSCP["fscp"], c=sub_df_FSCP["color_type"], edgecolor = "grey", zorder =2)
    # l1, = axes[1].plot(np.linspace(0,250), a*np.linspace(0,250) + b, c = fscp_color, alpha = 1, zorder = 1)


    # s2 = axes[1].scatter(sub_df_FSCP2["h2_LCO"], sub_df_FSCP2["fscp"], c=sub_df_FSCP2["color_type"], edgecolor = "grey", zorder = 1)
    # l2, = axes[1].plot(np.linspace(0,250), a2*np.linspace(0,250) + b2, c = fscp_color2, alpha = 1, zorder = 0)


    # ## extra annotations on bottom pannel- not sure if needed
    # # axes[1].vlines(intersection, 0,250,ls="--", color = "darkgrey")
    # # axes[1].text(80,175, "DRI-EAF is the\ncheapest mitigation option", color = "grey", horizontalalignment="center",
    # #              bbox=dict(facecolor = "white",edgecolor = "darkgrey", boxstyle="round,pad=0.5"))
    # # axes[1].text(147,175, "BF-BOF-CCS is the\ncheapest mitigation option", color = "grey",horizontalalignment="center",
    # #              bbox=dict(facecolor = "white",edgecolor = "darkgrey", boxstyle="round,pad=0.5"))

    # axes[1] = change_spines(axes[1])
    
    # axes[1].set_title("FSCP dependency on assumed H2 cost", fontweight="bold", loc ="left")
    # axes[1].set_ylabel(f"Fuel-switching CO2 price \n(EUR/tCO2)")
    # axes[1].set_xlabel(f"Hydrogen cost (EUR/MWh)")
    # axes[1].set_ylim(0, 200)
    # axes[1].set_xlim(0, 250)
    # axes[1].legend([(s1,l1), (s2,l2)],["DRI-EAF replacing BF-BOF steel","BF-BOF-CCS replacing BF-BOF steel"], loc = "lower right")

    fig.tight_layout()
    fig.savefig('././figs/supp_aviationfuelLCObreakdown.png', format='png', dpi = 200)
    #plt.show()

def calculate_em_abated(row, fossil_em, df):
    if row['type'] == 'comp':
        try:
            return df.loc[df['type'] == 'ccs', 'em'].values[0]
        except IndexError:
            return df.loc[df['type'] == 'h2', 'em'].values[0]
    elif row['type'] == 'ccs' or row['type'] == 'ccsretrofit' or row['type'] == 'h2':
        return fossil_em - row['em']
    
def hex_to_rgba(hex_color, alpha):
    rgb = colors.hex2color(hex_color)  # convert hex to rgb
    return (*rgb, alpha)  # convert rgb to rgba

def fscp_fractions(df, fossil_em):
    comp_row = df[df["type"] == "comp"]
    em_abated_comp_row = comp_row["em_abated"].values[0]
    fscp_comp_row = comp_row["fscp"].values[0]
    comp_fscp_frac = fscp_comp_row*em_abated_comp_row/fossil_em #in EUR/tCO2

    other_rows = df[df["type"] != "comp"]
    other_rows["fscp_frac"] = other_rows["fscp"]*other_rows["em_abated"]/fossil_em
    other_rows["comp_fscp_frac"] = comp_fscp_frac
    return other_rows

def plot_steel_macc(dfs, dfs_retrofit, dfs_comp, dfs_comp_retrofit, sector = "steel", type = "h2",sensitivity = "h2_LCO"):
    dfs = add_colors_units_rename(dfs)
    dfs_retrofit = add_colors_units_rename(dfs_retrofit)
    dfs_comp = add_colors_units_rename(dfs_comp)
    dfs_comp_retrofit = add_colors_units_rename(dfs_comp_retrofit)

    #filter df to get relevant LCOs
    sub_df_LCO = dfs[(dfs["sector"]==sector) & ((dfs["type"]==type) | (dfs["type"]=="comp") | (dfs["type"]=="ccs") )]


    retrofit_rows = dfs_retrofit[(dfs_retrofit["sector"]==sector) &  (dfs_retrofit["type"]=="ccs") ]
    retrofit_rows["type"] = "ccsretrofit"
    retrofit_rows["color_type"] = "#46bfeb"
    retrofit_rows = retrofit_rows.drop([ 'ccs_steel_capex', 'fossil_steel_capex'], axis = 1)

    sub_df_LCO = pd.concat([sub_df_LCO, retrofit_rows], ignore_index=True)

    #filter df to get relevant FSCP with comp, for the big line plot
    sub_df_FSCP = dfs_comp[(dfs_comp["sector"]==sector) & (dfs_comp["type"]==type) ]
    sub_df_FSCP2 = dfs_comp[(dfs_comp["sector"]==sector) & (dfs_comp["type"]=="ccs") ]
    sub_df_FSCP3 = dfs_comp_retrofit[(dfs_comp_retrofit["sector"]==sector) & (dfs_comp_retrofit["type"]=="ccs") ]
    sub_df_FSCP3["color_type"] = "#46bfeb"

    #for plot E, all fscps.
    sub_df_FSCP_nocomp = dfs[(dfs["sector"]==sector) & (dfs["type"]==type) ]
    sub_df_FSCP2_nocomp = dfs[(dfs["sector"]==sector) & (dfs["type"]=="ccs") ]
    sub_df_FSCP3_nocomp = dfs_retrofit[(dfs_retrofit["sector"]==sector) & (dfs_retrofit["type"]=="ccs") ]


    fscp_color = np.unique(sub_df_FSCP["color_type"])[0]
    fscp_color2 = np.unique(sub_df_FSCP2["color_type"])[0]
    fscp_color3 = "#46bfeb"
    fscp_color4 = np.unique(sub_df_LCO[sub_df_LCO["type"]=="comp"]["color_type"])

    
    unit = np.unique(sub_df_LCO["unit"])[0]
    fossil_em = dfs[(dfs["sector"]==sector) &  (dfs["type"]=="fossil")]["em"].unique()[0]
    
    #following line is a bit hacky, will make code break if comparing options with the same cost (eg DRI when choosing DAC Co2 sensitivity)
    sub_df_LCO.drop_duplicates( "cost", inplace=True)
    sub_df_LCO.reset_index(inplace=True, drop = True)
    sub_df_LCO.drop(["elec"], axis = 1, inplace = True)
    sub_df_LCO = sub_df_LCO.round(2)
    
    #merge to make final df
    sub_df_LCO_merge = sub_df_LCO

    # sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "comp") & (sub_df_LCO["type"] != "ccs"), "code"] = sub_df_LCO["code"] + ",\nH2 cost =\n" +sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh"
    sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "comp") & (sub_df_LCO["type"] != "ccs") & (sub_df_LCO["type"] != "ccsretrofit"), "annot"] = "H2 cost: "+sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh"

    #sort so the comp pathway is first
    # sub_df_LCO.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)
    sub_df_LCO_merge.loc[sub_df_LCO["type"]=="comp", "code"] = "Compensation of\nresidual emissions" 
    sub_df_LCO_merge.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)

    # fig = plt.figure(figsize=(12,10), layout = "constrained")
    # fig = plt.figure(figsize=(12,30), layout = "constrained", dpi= 70)
    fig = plt.figure(figsize=(18,22), layout = "constrained", dpi= 600)
    axes = fig.subplot_mosaic(
        """
        AABB
        CCCC
        CCCC
        DDDD
        DDDD
        """
    )

    #set font size
    SMALL_SIZE = 18
    MEDIUM_SIZE = 20
    BIGGER_SIZE = 22

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    plt.rc('axes', titlesize=BIGGER_SIZE)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)

    # make specific filtered dfs for different combinations of mitigation options
    sub_df_LCO_merge_CCS = sub_df_LCO_merge[(sub_df_LCO_merge["type"]=="ccs") |(sub_df_LCO_merge["type"]=="ccsretrofit") | (sub_df_LCO_merge["type"]=="comp") ]
    
    sub_df_LCO_merge_CCS['em_abated'] = sub_df_LCO_merge_CCS.apply(calculate_em_abated, args=(fossil_em, sub_df_LCO_merge_CCS), axis=1)
    sub_df_LCO_merge_CCS["annot"] = ["New plant", "Retrofit", ""] #last one in list was np.nan before

    #first, plot colorerd layer
    facecolors = sub_df_LCO_merge_CCS["color_type"].apply(lambda color: hex_to_rgba(color, 0.1))
    edgecolors = sub_df_LCO_merge_CCS["color_type"].apply(lambda color: hex_to_rgba(color, 1))
    bars = axes["A"].bar([0,0,1], sub_df_LCO_merge_CCS["fscp"], color = facecolors, edgecolor = edgecolors, width = sub_df_LCO_merge_CCS["em_abated"])

    # #add numbers
    # axes["A"].text(-0.3, 70, "1", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color3, "facecolor":"white"})
    # axes["A"].text(-0.3, 150, "2", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color2, "facecolor":"white"})
    # axes["A"].text(0.9, 350, "3", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color4[0], "facecolor":"white"})

    # #other plot settings
    # axes["A"].set_xticks([0,0,1], sub_df_LCO_merge_CCS["code"])
    
    # Set the x-ticks to the right side of the bars
    xticks = [bar.get_x() + bar.get_width() for bar in bars[1:]]
    axes["A"].set_xticks(xticks)

    # Set the x-tick labels to the 'code' values
    cumulative_em_abated = sub_df_LCO_merge_CCS["em_abated"].unique().cumsum().round(2)
    cumulative_em_abated = (np.rint(np.array(cumulative_em_abated *100 / cumulative_em_abated.max()))).astype(int)
    axes["A"].set_xticklabels(cumulative_em_abated, fontsize = 16)

    # Add 'code' values under the bars
    for bar, code in zip(bars, sub_df_LCO_merge_CCS["code"]):
        axes["A"].text(bar.get_x()+0.01 , 5, code, ha='left', va='bottom', rotation = 90, fontsize = 16)

    axes["A"] = change_spines(axes["A"])

    #add retrofit, New plant annotation
    for i, (fscp, annot) in enumerate(zip(sub_df_LCO_merge_CCS["fscp"], sub_df_LCO_merge_CCS["annot"])):
        if pd.isna(annot):
            continue
        axes["A"].text(0, fscp, annot, ha='center', va='bottom', color = "grey", fontsize = 16)

    axes["A"].set_ylim(0, 370)
    axes["A"].set_title("Marginal abatement cost curve for BF-BOF-CCS\nand CDR compensation combination,\nfor a retrofit and a new plant case.", loc = "left", weight = "bold")
    axes["A"].set_ylabel(f"Fuel-switching CO2 price\n(EUR/tCO2)", fontsize = 18)
    axes["A"].set_xlabel(f"% emissions mitigation compared to BF-BOF (w/o CCS)", fontsize = 18)
    
    sub_df_LCO_merge_h2 = sub_df_LCO_merge[(sub_df_LCO_merge["type"]=="h2") | (sub_df_LCO_merge["type"]=="comp") ]
    sub_df_LCO_merge_h2['em_abated'] = sub_df_LCO_merge_h2.apply(calculate_em_abated, args=(fossil_em, sub_df_LCO_merge_h2), axis=1)
    
    #first, plot colorerd layer
    facecolors = sub_df_LCO_merge_h2["color_type"].apply(lambda color: hex_to_rgba(color, 0.1))
    edgecolors = sub_df_LCO_merge_h2["color_type"].apply(lambda color: hex_to_rgba(color, 1))

    #bars = axes["B"].bar([0,0,0,0,1], sub_df_LCO_merge_h2["fscp"], color=facecolors, edgecolor=edgecolors, width=sub_df_LCO_merge_h2["em_abated"])
    bars = axes["B"].bar([0,0,1], sub_df_LCO_merge_h2["fscp"], color=facecolors, edgecolor=edgecolors, width=sub_df_LCO_merge_h2["em_abated"])
    
    # #add numbers
    # axes["B"].text(-0.5, 110, "4", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color, "facecolor":"white"})
    # axes["B"].text(-0.5, 200, "5", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color, "facecolor":"white"})
    # axes["B"].text(1, 350, "6", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color4[0], "facecolor":"white"})

    ##other plot settings
    #axes["B"].set_xticks([0,1], sub_df_LCO_merge_h2["code"].unique())
    
    # Set the x-ticks to the right side of the bars
    xticks = [bar.get_x() + bar.get_width() for bar in bars[1:]]
    axes["B"].set_xticks(xticks)

    # Set the x-tick labels to the 'code' values
    cumulative_em_abated = sub_df_LCO_merge_h2["em_abated"].unique().cumsum().round(2)
    cumulative_em_abated = (np.rint(np.array(cumulative_em_abated *100 / cumulative_em_abated.max()))).astype(int)
    axes["B"].set_xticklabels(cumulative_em_abated, fontsize = 16)

    # Add 'code' values under the bars
    for i, (bar, code) in enumerate(zip(bars[1:], sub_df_LCO_merge_h2["code"][1:])):
        if i == 1:
            axes["B"].text(bar.get_x()+0.01, 5, code, ha='left', va='bottom', rotation = 90, fontsize = 16)
        else:
            axes["B"].text(bar.get_x()+0.01 , 5, code, ha='left', va='bottom', rotation = 90, fontsize = 16)
    # bar.get_x() + bar.get_width() / 2
            
    axes["B"] = change_spines(axes["B"])

    for i, (fscp, annot) in enumerate(zip(sub_df_LCO_merge_h2["fscp"], sub_df_LCO_merge_h2["annot"])):
        if pd.isna(annot):
            continue
        axes["B"].text(0, fscp, annot, ha='center', va='bottom', color = "grey", fontsize = 16)

    axes["B"].set_ylim(0, 370)
    axes["B"].set_title("Marginal abatement cost curve for\nH2-DRI-EAF and CDR compensation combination,\nwith different H2 cost assumptions",loc = "left", weight = "bold")
    axes["B"].set_ylabel(f"Fuel-switching CO2 price\n(EUR/tCO2)", fontsize = 18)
    axes["B"].set_xlabel(f"% emissions mitigation compared to BF-BOF (w/o CCS)", fontsize = 18)

    #plot C

    sub_df_LCO_merge_CCS = fscp_fractions(sub_df_LCO_merge_CCS, fossil_em)
    sub_df_LCO_merge_h2 = fscp_fractions(sub_df_LCO_merge_h2, fossil_em)
    df_ccs_h2_fscpdiff = pd.concat([sub_df_LCO_merge_CCS.iloc[::-1],sub_df_LCO_merge_h2], ignore_index=True)

    df_ccs_h2_fscpdiff.loc[(df_ccs_h2_fscpdiff["type"] != "ccs") & (df_ccs_h2_fscpdiff["type"] != "ccsretrofit"), "annot"] = "H2-DRI-EAF,\nH2 cost: "+df_ccs_h2_fscpdiff["h2_LCO"].astype(str) + " EUR/MWh"
    df_ccs_h2_fscpdiff.loc[(df_ccs_h2_fscpdiff["type"] == "ccs"), "annot"] = "CCS: New plant"
    df_ccs_h2_fscpdiff.loc[(df_ccs_h2_fscpdiff["annot"] == "Retrofit"), "annot"] = "CCS: Retrofit"
    
    facecolors = df_ccs_h2_fscpdiff["color_type"].apply(lambda color: hex_to_rgba(color, 0.3))
    facecolor_comp = hex_to_rgba(fscp_color4[0], 0.3)

    bar1 = axes["C"].bar(df_ccs_h2_fscpdiff['annot'], df_ccs_h2_fscpdiff['fscp_frac'], color = facecolors, edgecolor = df_ccs_h2_fscpdiff["color_type"], width = 0.5)
    bar2 = axes["C"].bar(df_ccs_h2_fscpdiff['annot'], df_ccs_h2_fscpdiff['comp_fscp_frac'], bottom = df_ccs_h2_fscpdiff['fscp_frac'],color = facecolor_comp,edgecolor = fscp_color4, width = 0.5)
    
    #annotate bars
    for i, (b1, b2, col) in enumerate(zip(bar1, bar2, df_ccs_h2_fscpdiff["color_type"]), start=1):
        height = b1.get_height() + b2.get_height()
        # Adding the total height line
        axes["C"].plot([b1.get_x() + b1.get_width(), b1.get_x() + b1.get_width() + 0.1], 
                [height, height], color='grey')

        axes["C"].plot([b1.get_x() + b1.get_width()+0.05, b1.get_x() + b1.get_width() + 0.05], 
                [0, height], color='grey')
        # Adding the label next to the total height line
        axes["C"].text(b1.get_x() + b1.get_width() + 0.1, height /2, str(i), color='grey', bbox={"boxstyle" : "circle", "edgecolor": col, "facecolor":"white"})
    # #add numbers
    # axes["C"].text(0, 18, "1", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color3, "facecolor":"white"})
    # axes["C"].text(0, 110, "3", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color4[0], "facecolor":"white"})
    # axes["C"].text(1, 42, "2", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color2, "facecolor":"white"})
    # axes["C"].text(1, 170, "3", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color4[0], "facecolor":"white"})
    # axes["C"].text(2, 60, "4", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color, "facecolor":"white"})
    # axes["C"].text(2, 120, "6", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color4[0], "facecolor":"white"})
    # axes["C"].text(3, 100, "5", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color, "facecolor":"white"})
    # axes["C"].text(3, 205, "6", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color4[0], "facecolor":"white"})

    axes["C"] = change_spines(axes["C"])
    #make legend
    legend_els = [
        Patch(facecolor=hex_to_rgba(fscp_color3, 0.3), edgecolor=fscp_color3, label='BF-BOF-CCS (retrofit)'),
        Patch(facecolor=hex_to_rgba(fscp_color2, 0.3), edgecolor=fscp_color2, label='BF-BOF-CCS (new plant)'),
        Patch(facecolor=hex_to_rgba(fscp_color, 0.3), edgecolor=fscp_color, label='H2-DRI-EAF'),
        Patch(facecolor=hex_to_rgba(fscp_color4[0], 0.3), edgecolor=fscp_color4[0], label='CDR compensation')
    ]

    box = axes["C"].get_position()
    axes["C"].set_position([box.x0-0.06, box.y0-0.02, box.width * 0.85, box.height* 1])
    axes["C"].legend(handles = legend_els, bbox_to_anchor=(1.0, 0.05), loc="lower left", borderaxespad=0)


    axes["C"].set_title("Total fuel-switching CO2 price for full mitigation, with its different components",loc = "left", weight = "bold")
    axes["C"].set_ylabel(f"Fuel-switching CO2 price\n(EUR/tCO2)", fontsize = 18)
    axes["C"].set_ylim(0, 260)


    #now, FSCP figure
    FSCP = axes["D"]
    #calc best fit linear
    
    #find line of best fit
    a, b = np.polyfit(sub_df_FSCP["h2_LCO"], sub_df_FSCP["fscp"], 1)
    a2, b2 = np.polyfit(sub_df_FSCP2["h2_LCO"], sub_df_FSCP2["fscp"], 1)
    a3, b3 = np.polyfit(sub_df_FSCP3["h2_LCO"], sub_df_FSCP3["fscp"], 1)
    intersection = (b2-b)/(a-a2)
    a4, b4 = np.polyfit(sub_df_FSCP_nocomp["h2_LCO"], sub_df_FSCP_nocomp["fscp"], 1)
    a5, b5 = np.polyfit(sub_df_FSCP2_nocomp["h2_LCO"], sub_df_FSCP2_nocomp["fscp"], 1)
    a6, b6 = np.polyfit(sub_df_FSCP3_nocomp["h2_LCO"], sub_df_FSCP3_nocomp["fscp"], 1)


    #s1 = FSCP.scatter(sub_df_FSCP["h2_LCO"], sub_df_FSCP["fscp"], c=sub_df_FSCP["color_type"], edgecolor = "grey", zorder =2)
    l1, = FSCP.plot(np.linspace(0,250), a*np.linspace(0,250) + b, c = fscp_color, alpha = 1, zorder = 1)

    #s2 = FSCP.scatter(sub_df_FSCP2["h2_LCO"], sub_df_FSCP2["fscp"], c=sub_df_FSCP2["color_type"], edgecolor = "grey", zorder = 1)
    l2, = FSCP.plot(np.linspace(0,250), a2*np.linspace(0,250) + b2, c = fscp_color2, alpha = 1, zorder = 0)

    #s3 = FSCP.scatter(sub_df_FSCP3["h2_LCO"], sub_df_FSCP3["fscp"], c=fscp_color3, edgecolor = "grey", zorder = 1)
    l3, = FSCP.plot(np.linspace(0,250), a3*np.linspace(0,250) + b3, c = fscp_color3, alpha = 1, zorder = 0)

    l4, = FSCP.plot(np.linspace(0,250), a4*np.linspace(0,250) + b4, c = fscp_color, alpha = 1, zorder = 1, linestyle='--')
    l5, = FSCP.plot(np.linspace(0,250), a5*np.linspace(0,250) + b5, c = fscp_color2, alpha = 1, zorder = 0, linestyle='--')
    l6, = FSCP.plot(np.linspace(0,250), a6*np.linspace(0,250) + b6, c = fscp_color3, alpha = 1, zorder = 0, linestyle='--')

    #break-even H2 point calculation
    #break-even full comp: h2-ccs(new)
    x_i2 = (b2-b)/(a-a2)
    m1, = FSCP.plot(x_i2, a*x_i2 +b, color = "darkgrey", marker = 'v', markersize = 18, linestyle='None')
    #break-even full comp: h2-ccs(retrofit)
    x_i3 = (b3-b)/(a-a3)
    FSCP.plot(x_i3, a*x_i3 +b, color = "darkgrey", marker = 'v', markersize = 18)
    #break-even partial comp: h2-ccs(new)
    x_i5 = (b5-b4)/(a4-a5)
    m2, = FSCP.plot(x_i5, a4*x_i5 +b4, color = "darkgrey", marker = 's', markersize = 16, linestyle='None')
    #break-even partial comp: h2-ccs(retrofit)
    x_i6 = (b6-b4)/(a4-a6)
    FSCP.plot(x_i6, a4*x_i6 +b4, color = "darkgrey", marker = 's', markersize = 16)
    
    #number markers for correspondence with plot C
    FSCP.text(120, a3*120 + b3-2, "1", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color3, "facecolor":"white"})
    FSCP.text(120, a2*120 + b2-2, "2", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color2, "facecolor":"white"})
    FSCP.text(100, a*100 + b-2, "3", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color, "facecolor":"white"})
    FSCP.text(200, a*200 + b-2, "4", ha='center', va='bottom', color ="grey", bbox={"boxstyle" : "circle", "edgecolor": fscp_color, "facecolor":"white"})

    FSCP = change_spines(FSCP)
    
    FSCP.set_title("Fuel-switching CO2 price dependency on assumed H2 cost", loc ="left", weight = "bold")
    FSCP.set_ylabel(f"Fuel-switching CO2 price \n(EUR/tCO2)", fontsize = 18)
    FSCP.set_xlabel(f"Hydrogen cost (EUR/MWh)", fontsize = 18)
    #FSCP.set_ylim(0, 255)
    #FSCP.set_xlim(0, 255)
    
    # Get the current position of the subplot
    box = FSCP.get_position()

    # # Adjust the position of the subplot
    # # The values are in fractions of the figure width and height
    # FSCP.set_position([box.x0-0.05, box.y0-0.08, box.width * 0.85, box.height* 0.85])
    FSCP.set_position([box.x0-0.06, box.y0-0.02, box.width * 0.85, box.height* 0.85])
    FSCP.legend([(l1), (l2), (l3), (l4), (l5), (l6), (m1), (m2)],
                ["H2-DRI-EAF + CDR \n(full mitigation)",
                 "BF-BOF-CCS + CDR \n(full mitigation, new plant)",
                 "BF-BOF-CCS + CDR \n(full mitigation, retrofit)",
                 "H2-DRI-EAF \n(incomplete mitigation)",
                 "BF-BOF-CCS \n(incomplete mitigation,\nnew plant)",
                 "BF-BOF-CCS \n(incomplete mitigation, retrofit)",
                 "Break-even points\n(full mitigation)",
                 "Break-even points\n(incomplete mitigation)"],
                bbox_to_anchor=(1.0, 0.05), loc="lower left", borderaxespad=0,
                #bbox_to_anchor=(0.84, 0.05), loc="lower left", borderaxespad=0,
                ncol = 1)


    for n,ax in enumerate(axes.values()):
        plt.setp(ax.get_yticklabels(), fontsize=18)
        plt.setp(ax.get_xticklabels(), fontsize=18)
        ax.text(-0.1, 1.05, string.ascii_lowercase[n], transform=ax.transAxes, 
                    size=20, weight='bold')

    #fig.tight_layout()
    #plt.show()
    # fig.savefig('././myimage.svg', format='svg', dpi=1200)
    fig.savefig('././figs/main_steelFSCP.png', format='png', dpi = 200)
    
def blueh2_costanalysis(dfs):
    blueh2_rows = []
    for df in dfs:
        filtered_df = df[df["tech"] == "blueh2"]
        blueh2_rows.append(filtered_df)
    blueh2_df = pd.concat(blueh2_rows, ignore_index=True)
    
    co2cost = 200 #EUR/tCO2
    GWP100 = 34 #CO2 equivalent
    NG_lhv = 13.1 #kWh/kg or MWh/ton

    #calculate extra cost from 0.1% leakage:
    low_leakage_cost = 0.001*(1/NG_lhv)*co2cost*GWP100
    high_leakage_cost = 0.03*(1/NG_lhv)*co2cost*GWP100
    
    blueh2_lowleakage = blueh2_df["cost"] + low_leakage_cost
    blueh2_highleakage = blueh2_df["cost"] + high_leakage_cost

    #Green LCOH: 1-2.5USD/kg according to IEA NZE, conversion rate 1 USD = 0.89 EUR
    #other source: 1.3 - 3.3 USD/kg (https://www.iea.org/data-and-statistics/charts/global-average-levelised-cost-of-hydrogen-production-by-energy-source-and-technology-2019-and-2050)
    greenh2_cost = np.array([26.7,34.71,66.75,88.11]) 
    
    fig = plt.figure(figsize=(8, 6))
    box_plot = plt.boxplot([greenh2_cost,blueh2_df["cost"], blueh2_lowleakage, blueh2_highleakage ], patch_artist=True)#, boxprops=dict(facecolor=['skyblue', color='black'), whiskerprops=dict(color='black'), capprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='r', markersize=8, linestyle='none'))
    
    colors = ['lightgreen', 'skyblue','royalblue','darkblue' ]

    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)

    ax = plt.gca()
    ax = change_spines(ax)
    
    plt.ylim(0, 120)
    plt.ylabel("Low-emission H2 cost\n(EUR/MWh)")
    plt.xticks([1, 2,3,4], ["Green H2\n(IEA NZE 2050)", "Blue H2", "Blue H2, \n0.1"+'%'+" leakage", "Blue H2, \n3"+'%'+" leakage"])
    plt.title('Cost of various low-emission hydrogen production pathways',fontsize = 14, fontweight='bold', loc='left')
    fig.savefig('././figs/supp_blueH2cost.png', format='png', dpi = 200)

def nonfossilco2_supplycurve():
    CO2_source = np.array(["Bioethanol", "Biogas", "Pulp and paper", "Waste-to-energy", "Biomass\nheat and power", "Direct-air capture"])
    amount = np.array([0.3,0.15,0.38,0.84,2.5,5]) #in GtCO2/yr
    cost = np.array([40.8,20.1,52.65,36,165.6,400]) #in EUR/tCO2
    color = np.array(['#3fa34d', '#137547', '#72b01d', '#054a29', '#2a9134', "#FEB380"])

    CO2_df = pd.DataFrame({"CO2_source": CO2_source, "amount": amount, "cost": cost, "color": color})
    CO2_df = CO2_df.sort_values(by = "cost")

    #build the supply curve
    x_positions = [0]  # Start at 0
    for width in CO2_df['amount'][:-1]:  # Add cumulative sum of widths for each step
        x_positions.append(x_positions[-1] + width)

    # Plotting the step plot
    fig = plt.figure(figsize=(10, 6))
    #plt.step(x_positions, CO2_df['cost'], where='post', color='blue', linewidth=2)
    for x, height, width, color, name in zip(x_positions, CO2_df['cost'], CO2_df['amount'], CO2_df['color'], CO2_df['CO2_source']):
        plt.bar(x, height, width=width, color=color, align='edge', edgecolor='black')
        
        rect_center_x = x + width / 2
        # Add annotation text above each rectangle

        if name != "Direct-air capture":    
            plt.annotate(
                name,
                (rect_center_x, height),  
                textcoords="offset points",  
                xytext=(0, 20),
                ha='center',
                ma = "left",  
                rotation=90,  
                fontsize=10,  
                arrowprops=dict(arrowstyle='-', color='black')  
            )
        else:
            plt.annotate(
                name,
                (rect_center_x-1, height),  
                textcoords="offset points",  
                xytext=(0, 10),
                ha='right',  
                rotation=0,  
                fontsize=10,    
            )
    
    #extend plot to the right
    # Extend the x-axis with a dotted line
    #end_of_plot = sum(CO2_df['amount'])
    end_of_plot = 8
    x_axis_end = end_of_plot + 2  # Extend beyond the sum of widths
    plt.plot([end_of_plot, x_axis_end], [0, 0], 'k--', linewidth=1)  # Dotted line

    # Fading out rectangle outside the axes
    #rightmost_x = x_positions[-1] + CO2_df['amount'].iloc[-1]
    rightmost_x = end_of_plot
    rightmost_height = CO2_df['cost'].iloc[-1]
    fade_width = 0.9

    # Create a faded effect using a gradient
    fade = np.linspace(0, 1, 100)  # Gradient fade from 1 to 0
    for i in range(100):
        plt.bar(rightmost_x + (i * fade_width / 100), rightmost_height,
                width=fade_width / 100, color="white", alpha=fade[i],
                align='edge', edgecolor='none')
    
    
    # Add thin rectangles at the top of the figure
    ax = plt.gca()
    cumulative_width1 = 2.8  # Example width for the first thin rectangle
    cumulative_width2 = 2.2  # Example width for the second thin rectangle
    top_rect_height = 60  # Thin height for the top rectangles
    top_y_position = max(CO2_df['cost']) * 1.3  # Position above the tallest bar

    # # Create the first thin rectangle
    # rect1 = Rectangle((0, top_y_position), cumulative_width1, top_rect_height, 
    #                         linewidth=1, edgecolor='black', facecolor='lightgrey')
    
    # ax.add_patch(rect1)

    

    # # Create the second thin rectangle, right next to the first one
    # rect2 = Rectangle((cumulative_width1, top_y_position), cumulative_width2, top_rect_height, 
    #                         linewidth=1, edgecolor='black', facecolor='lightgrey')
    # ax.add_patch(rect2)
    
    # arrow1 = FancyArrow(x=0, y=top_y_position, dx=cumulative_width1, dy=0, 
    #                         width=top_rect_height, head_width=top_rect_height * 2, 
    #                         head_length=0.1, length_includes_head=True, 
    #                         edgecolor='black', facecolor='lightgrey')

    #the +/- 0.05 on the width account for the arrow head size
    arrow1 = FancyArrowPatch((0, top_y_position), (cumulative_width1+0.05, top_y_position),
                                 arrowstyle='<->', mutation_scale=15, color='darkgrey', lw=2)
    ax.add_patch(arrow1)

    arrow2 = FancyArrowPatch((cumulative_width1-0.05 , top_y_position), (cumulative_width1+cumulative_width2+0.05, top_y_position),
                                 arrowstyle='<->', mutation_scale=15, color='darkgrey', lw=2)
    ax.add_patch(arrow2)
    # Add 1st annotation
    plt.text(cumulative_width1 / 2, top_y_position - top_rect_height / 2, "E-chemical CO2 demand\n(2050)", 
            ha='center', va='center', fontsize=10, color = "dimgrey")
    # Add 2nd annotation
    plt.text(cumulative_width1 + cumulative_width2 / 2, top_y_position - top_rect_height / 2, "E-fuel CO2 demand\n(2050)", 
            ha='center', va='center', fontsize=10, color = "dimgrey")

    #add vline displaying total demand in 2050
    plt.axvline(x=cumulative_width1 + cumulative_width2, ymin = 0, ymax = top_y_position, color='darkgrey', linestyle='--')
    #plot limits
    #plt.xlim(0, 7)
    plt.xlim(0, end_of_plot + fade_width)
    plt.ylim(0, max(CO2_df['cost']) * 1.5)

    # Adding grid and labels
    ax = fig.get_axes()[0]
    ax = change_spines(ax)
    plt.xlabel('Theoretical quantity availably by 2050 (GtCO2/yr)')
    plt.ylabel('Cost (EUR/tCO2)')
    plt.title('Non-fossil CO2 Supply Curve', fontsize=14,fontweight='bold', loc='left')
    fig.savefig('././figs/supp_nonfossilCO2supplycurve.png', format='png', dpi = 200)