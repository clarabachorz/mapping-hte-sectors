import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.colors import to_rgba
from matplotlib.ticker import FormatStrFormatter
import matplotlib.gridspec as gridspec
from  matplotlib.cm import ScalarMappable
from  matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# plt.rcParams["font.family"] = "Calibri"
# plt.rcParams.update({
#     "text.usetex": True,
#     "font.family": "Helvetica"
# })

matplotlib.rcParams.update(matplotlib.rcParamsDefault)

#plot parameters, colors, text
rename_sectors = {"cement": "Cement", "steel" : "Steel", "ship" : "Maritime", "plane" : "Aviation", "chem" : "Chemical feedstocks (CF)" }
#ordering of technology types (h2, ccs, ccu etc)
order_types = ["fossil", "h2", "efuel", "ccu", "ccs", "comp" ]
#colors
color_dict = {"cement":"#EABE7C", "steel":"#8c6570","ship":"#0471A6","plane":"#61E8E1", "chem":"#AFB3F7"}
color_dict_tech = {"fossil":"#31393C", "h2": "#FCE762", "efuel": "#FEB380", "comp":"#23CE6B", "ccu":"#8E9AAF", "ccs":"#3083DC"}
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

def plot_large_panel_wMACC(dfs):

    dfs = add_colors_units_rename(dfs)
    dfs = sort_data(dfs)
    ## First 3 rows: subplots
    fig, axes = plt.subplots(nrows = 6,ncols=5, figsize=(3*5,3*5))
    idx = 0
    for name, df in dfs.groupby("sector", sort = False):
        unit = np.unique(df["unit"])[0]
        color_sector = np.unique(df["color_sector"])[0]

        df = df.reset_index()
        axes[0,idx].bar(df["code"], df["cost"], color = df["color_sector"], edgecolor = "grey")
        #axes[0,idx].bar(df["code"], df["cost"], color = df["color_type"], edgecolor = "grey")

        #look for nans (ie missing technologies)
        nan_idx = np.where(df['cost'].isnull())[0]
        axes[0,idx].bar(df["code"][nan_idx], np.nanmax(df["cost"])+100, facecolor='white',  hatch='/', edgecolor = "lightgrey")

        #make axes nicer
        #axes[0,idx] = change_spines(axes[0,idx])
        #add a couple of parameters
        axes[0,idx].set_title(name)#, backgroundcolor = color_sector , position=(0.5, 0.5))
        axes[0,idx].set_ylabel(f"Levelized cost \n(EUR{unit})")
        axes[0,idx].set_ylim(0, np.nanmax(df["cost"])*1.05)

        #axes[0,idx].patch.set_facecolor(color_sector)
        #axes[0,idx].patch.set_alpha(0.7)

        axes[0,idx].tick_params(rotation=90)


        #calculate max emissions and use to scale alpha of barplot
        max_em = np.nanmax(df["em"].to_numpy())

        ems_rel =[]
        for perc in df["em"].to_numpy():
            if perc >0:
                ems_rel.append(to_rgba('grey', alpha=np.abs(perc) / max_em))
            else:
                ems_rel.append(to_rgba('grey', alpha=0))
        
        #plot emissions
        #axes[1,idx].bar(df["code"], df["em"], color = [to_rgba('grey', alpha=np.abs(perc) / max_em) for perc in df["em"].to_numpy()], edgecolor = "grey")
        axes[1,idx].bar(df["code"], df["em"], color = ems_rel, edgecolor = "grey")
        #axes[1,idx] = change_spines(axes[1,idx])

        #look for nans
        nan_idx = np.where(df['em'].isnull())[0]
        axes[1,idx].bar(df["code"][nan_idx], np.nanmax(df["em"])+10, facecolor='white', hatch='/', edgecolor = "lightgrey")
        axes[1,idx].bar(df["code"][nan_idx], -np.nanmax(df["em"]), facecolor='white', hatch='/', edgecolor = "lightgrey")
        axes[1,idx].axhline(0, color='black', lw = 0.75)

        axes[1,idx].set_ylabel(f"CO2 emissions \n (tCO2{unit})")
        #axes[1,idx].set_ylim(np.nanmin(df["em"])*1.05, np.nanmax(df["em"])*1.05)
        axes[1,idx].set_ylim(-max_em*0.5, max_em*1.05)
        axes[1,idx].tick_params(rotation=90)

        #share axis between line 1 & 2
        axes[1,idx].sharex(axes[0,idx])
        #extra line that goes toogether with sharex to remove the x labels for the first row
        plt.setp(axes[0,idx].get_xticklabels(), visible=False)

        #plot fscp
        axes[2,idx].bar(df["code"], df["fscp"], color = df["color_sector"] ,edgecolor = "grey") 
        #axes[2,idx].bar(df["code"], df["fscp"], color = df["color_type"] ,edgecolor = "grey")
        #axes[2,idx] = change_spines(axes[2,idx])


        max_fscp = np.nanmax(dfs["fscp"].to_numpy())
        #look for nans (ie missing technologies)
        nan_idx = np.where(df['fscp'].isnull())[0]
        axes[2,idx].bar(df["code"][nan_idx], max_fscp * 1.1, facecolor='white', hatch='/', edgecolor = "lightgrey")
        #index = 0 corresponds to the fossil option
        axes[2,idx].bar(df["code"][0], max_fscp * 1.1, facecolor='white', hatch='/', edgecolor = "black")

        axes[2,idx].set_ylabel(f"FSCP (EUR/tCO2)")  
        axes[2,idx].set_ylim(0, np.nanmax(df["fscp"])*1.05)
        #share axis between line 1 & 2
        axes[2,idx].sharex(axes[1,idx])
        
        # # Use this to share y axis
        # if idx > 0:
        #     axes[2,idx].sharey(axes[2,0])
        #     axes[2,idx].set_ylabel(None)
        axes[2,idx].tick_params(rotation=90)

        #extra line that goes toogether with sharex to remove the x labels for the first row
        plt.setp(axes[1,idx].get_xticklabels(), visible=False) 
        
        #hacky way to remove unneeded plots
        fig.delaxes(axes[3, idx]) 
        fig.delaxes(axes[4, idx])
        fig.delaxes(axes[5, idx])         
        #step to next iteration
        idx += 1


    #the big figure: MACC curve#
    MACC1 = plt.subplot(2,1,2)

    #order the barplot here
    #dfs = dfs.sort_values(by = ["iea_energy","sector", "type"])
    dfs = dfs[dfs["fscp"].notna()]
    #dfs = dfs.sort_values(by = ["iea_energy","sector", "fscp"])
    dfs = dfs.sort_values(by = ["fscp"])


    w = dfs["iea_energy"].to_numpy()

    #make barplot show as nice rectangles stuck together
    xticks=[]
    bin_start=[]

    ### use this to have every single rectangle next to one another
    for n, c in enumerate(w):
        xticks.append(sum(w[:n]) + w[n]/2)
        bin_start.append(sum(w[:n]))
    bin_start.append(bin_start[-1]+ w[-1])

    #dfs["xticks"] = xticks
    
    #make barplot
    a = MACC1.bar( x=xticks, height= dfs["fscp"], width= dfs["iea_energy"], 
                  #fill = True ,edgecolor = "grey", color = dfs["color_type"], alpha = 1, label = dfs["type"])
                    fill = False , edgecolor = dfs["color_sector"],linewidth = 2, alpha = 1, label = dfs["sector"])
    #use this to swap xticks from energy to "info"
    _ = MACC1.set_xticks(xticks, dfs["info"],rotation=90, fontsize = 10)



    # #CODE BELOW: annotates each of the rectangles
    # for idx, bar in enumerate(a.patches):
    #     lab = dfs["sector"].to_numpy()[idx]
    #     col = dfs["color_sector"].to_numpy()[idx]
    #     #format(bar.get_height(), '.2f') to write height
    #     # to center in y at the middle: bar.get_height()/2 and va="center"
    #     #bar.get_label()
    #     # annotations.append(plt.annotate(lab, (bar.get_x() , bar.get_height()), 
    #     #                                 ha='center',va='center',  size=6, xytext=(0, 8), textcoords='offset points', rotation= 0, color = col))
    #     annotations.append(MACC1.text(bar.get_x()+bar.get_width() / 2 , bar.get_height() ,lab, va='center', 
    #                     size=7, rotation= 0,color = "black", bbox=dict(boxstyle="square,pad=0.3",fc=col, ec = "black" )))

    # #neat function to adjust annotation position so they dont overlap
    # adjust_text(annotations)

    #plt.bar_label(a, dfs["type"])

    #make legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))

    
    MACC1.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5),
             ncol=1, fancybox=True, shadow=True, prop={'size': 10})
    # MACC1.legend(by_label.values(), ["E-fuels", "H2/NH3","CCU", "CCS","DACCS \n(compensation)"], loc='center left', bbox_to_anchor=(1, 0.5),
    #          ncol=1, fancybox=True, shadow=True, prop={'size': 10})


    #add second axis
    MACC1_ax2 = MACC1.twiny()
    #MACC1_ax2.set_xticks(np.linspace(0,sum(w[:-1])+w[-1],2))
    MACC1_ax2.set_xticks(bin_start)
    
    MACC1_ax2.set_xlabel("Energy end-use (in EJ)")

    MACC1.set_xlim(0, bin_start[-1])
    MACC1_ax2.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    MACC1.set_ylim(0)
    MACC1.set_ylabel(f"Fuel-switching CO2 price (EUR/tCO2)")
    #MACC1.legend()

    ### SECOND MACC: emissions ###
    # MACC2 = plt.subplot(3,1,3)

    # dfs = dfs.sort_values(by = ["iea_em","sector", "fscp"])
    # w = dfs["iea_em"].to_numpy()

    # #make barplot show as nice rectangles stuck together
    # xticks=[]
    # for n, c in enumerate(w):
    #     xticks.append(sum(w[:n]) + w[n]/2)

    # #make barplot
    # a = MACC2.bar( x=xticks, height= dfs["fscp"], width= dfs["iea_em"], 
    #                   color = dfs["color_type"] , edgecolor = "grey", alpha = 0.8, label = dfs["sector"])
    # #use this to swap xticks from energy to "tech"
    # _ = MACC2.set_xticks(xticks, dfs["info"],rotation=90, fontsize = 8)

    # #make legend
    # handles, labels = plt.gca().get_legend_handles_labels()
    # by_label = dict(zip(labels, handles))
    # MACC2.legend(by_label.values(), by_label.keys(),loc= "upper right",
    #           ncol=1, fancybox=True, shadow=True, prop={'size': 10})
    # # MACC2.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5),
    # #           ncol=1, fancybox=True, shadow=True, prop={'size': 10})

    # #add second axis
    # MACC2_ax2 = MACC2.twiny()
    # MACC2_ax2.set_xticks(np.linspace(0,sum(w[:-1])+w[-1],13))
    # MACC2_ax2.set_xlabel("CO2 emissions (in Gt)")

    # MACC2.set_xlim(0, max(xticks)+ max(w)/2)
    # MACC2.set_ylabel(f"Fuel-switching CO2 price (EUR/tCO2)")

    ### PLOT FULL FIGURE ###
    #fig.suptitle(f"Parameters: $c_{{elec}} = {elec_cost}$ EUR/MWh, $c_{{DAC}} = {dac_cost:.0f}$ EUR/tCO2, $c_{{co2t&s}} = {co2_transport_storage}$ EUR/tCO2. Carbon tax of ${carbon_tax}$ EUR/tCO2. \n Abatement options for:")
    h2_LCO = dfs["h2_LCO"].unique()[0]
    co2_LCO = dfs["co2_LCO"].unique()[0]
    co2ts_LCO = dfs["co2ts_LCO"].unique()[0]
    fig.suptitle(f"Parameters projection for 2040: $c_{{h2}} = {h2_LCO}$ EUR/MWh, $c_{{DAC}} = {co2_LCO:.0f}$ EUR/tCO2, $c_{{co2t&s}} = {co2ts_LCO}$ EUR/tCO2. \n Abatement options for:")

    fig.tight_layout()
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.4, hspace=0.9)
    plt.show()

def plot_large_panel(dfs):
    dfs = add_colors_units_rename(dfs)
    dfs = sort_data(dfs)
    ## First 3 rows: subplots
    fig, axes = plt.subplots(nrows = 3,ncols=5, figsize=(18,15))

    idx = 0
    for name, df in dfs.groupby("sector", sort = False):
        unit = df["unit"].iloc[0]
        color_sector = np.unique(df["color_sector"])[0]

        df = df.reset_index()
        
        axes[0,idx].bar(df["code"], df["lco_noh2co2"], color = df["color_type"], edgecolor = "grey")

        axes[0,idx].bar(df["code"], df["co2_cost"], bottom =df["lco_noh2co2"]  ,color = df["color_type"], alpha = 0.8, hatch = '////', edgecolor = "grey", label = "co2")
        axes[0,idx].bar(df["code"], df["h2_cost"], bottom =df["lco_noh2co2"] +df["co2_cost"],color = df["color_type"], alpha = 0.8, hatch = '++', edgecolor = "grey", label = "h2")

        #look for nans (ie missing technologies)
        nan_idx = np.where(df['cost'].isnull())[0]
        axes[0,idx].bar(df["code"][nan_idx], np.nanmax(df["cost"])*1.05, facecolor='white',  hatch='/', edgecolor = "lightgrey")

        #make axes nicer
        axes[0,idx] = change_spines(axes[0,idx])
        #add a couple of parameters
        axes[0,idx].set_title(rename_sectors[name])#, backgroundcolor = color_sector , position=(0.5, 0.5))
        # if idx == 0:
        #     axes[0,idx].set_ylabel(f"Levelized cost \n(EUR{unit})")
        axes[0,idx].set_ylabel(f"Levelized cost \n(EUR{unit})")
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
        axes[1,idx].set_ylabel(f"CO2 emissions \n (tCO2{unit})")
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
        axes[2,idx].tick_params(rotation=90)

        #extra line that goes toogether with sharex to remove the x labels for the first row
        plt.setp(axes[1,idx].get_xticklabels(), visible=False)

                 
        #step to next iteration
        idx += 1


    #colorbar function
    colors_tech = {k: color_dict_tech[k] for k in ('h2', 'efuel', 'comp', 'ccu', 'ccs')}
    cmap = ListedColormap(colors_tech.values())

    fig.subplots_adjust(right=0.9)
    cbar_ax = fig.add_axes([0.92, 0.2, 0.02, 0.5])

    colbar = fig.colorbar(ScalarMappable( cmap=cmap), cax = cbar_ax)

    colbar.set_ticks([0.1, 0.3, 0.5, 0.7, 0.9])
    colbar.set_ticklabels(['H2/NH3', 'E-fuel','DACCS\ncompen-\nsation', 'CCU', 'CCS'])


    h2_patch = Patch(facecolor='white', edgecolor='grey', label='Green H2', hatch='+++')
    #co2ts_patch = Patch(facecolor='white', edgecolor='grey', label='CO2 transport\n and storage',hatch ='////')
    co2_patch = Patch(facecolor='white', edgecolor='grey', label='CO2 from DAC',hatch ='////')
    fig.legend(handles=[h2_patch,co2_patch], title = "Cost contributions",bbox_to_anchor=(0.51, 0.35, 0.49, 0.5))
    ### PLOT FULL FIGURE ###
    h2_LCO = dfs["h2_LCO"].unique()[0]
    co2_LCO = dfs["co2_LCO"].unique()[0]
    fig.suptitle(f"Abatement cost for the HTE sectors, based on optimistic parameter projection for 2050.\nCost of green H2: {h2_LCO} EUR/MWh, cost of CO2 from DAC: {co2_LCO:.0f} EUR/tCO2.")
    #fig.tight_layout()
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.55, hspace=0.2)
    plt.show()


def plot_barplotfscp(dfs, dfs_breakdown, sector = "steel", type = "h2",sensitivity = "h2_LCO"):
    dfs = add_colors_units_rename(dfs)
    dfs_breakdown[["type", "sector"]] = dfs_breakdown["tech"].str.split("_", expand=True)

    #filter df to get relevant LCOs
    sub_df_LCO = dfs[(dfs["sector"]==sector) & ((dfs["type"]==type) | (dfs["type"]=="fossil") | (dfs["type"]=="ccs") )]
    sub_df_LCO_breakdown = dfs_breakdown[(dfs_breakdown["sector"]==sector) & ((dfs_breakdown["type"]==type) | (dfs_breakdown["type"]=="fossil") | (dfs_breakdown["type"]=="ccs") )]

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
    sub_df_LCO_breakdown = sub_df_LCO_breakdown.drop_duplicates("LCO").dropna(axis=1, how='all').reset_index(drop = True).apply(pd.to_numeric, errors='ignore').round(2)
    sub_df_LCO_breakdown.rename(columns = {"LCO": "cost"}, inplace = True)
    sub_df_LCO_breakdown.drop(["type", "sector", "tech"], axis =1, inplace = True)
    sub_df_LCO_breakdown = sub_df_LCO_breakdown[[ "cost", "capex", "other costs", "elec","fossilng", "h2", "fossilccoal", "fossilpci", "co2 transport and storage"]]
    
    #merge to make final df
    sub_df_LCO_merge = sub_df_LCO.merge(sub_df_LCO_breakdown,how ="left",  on =[ "cost"],validate = "1:1")
    
    # sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "ccs"), "code"] = sub_df_LCO["code"] + ",\nH2 cost =\n" +sub_df_LCO["h2_LCO"].astype(str) + " EUR/MWh"
    sub_df_LCO_merge.loc[(sub_df_LCO["type"] != "fossil") & (sub_df_LCO["type"] != "ccs"), "code"] = sub_df_LCO["h2_LCO"].astype(str) + " \nEUR/MWh"

    #sort so the fossil pathway is first
    sub_df_LCO.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)
    sub_df_LCO_merge.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)

    fig, axes = plt.subplots(nrows = 2,ncols=1, figsize=(11,10))

    x_pos = [0,3,6,7.5,9,10.5]

    height = 0
    alpha_list = [0.75, 0.6, 0.45, 0.3, 0.2, 0.1, 0, 0.5]
    color = ["white", "white", "white", "white", "white", "white","white", "darkgrey"]
    labels = {"capex":"CAPEX", "other costs":"other OPEX\n(O&M, iron ore,\nscrap, ferroalloys)", "elec":"Electricity","fossilng": "Natural gas", "h2":"Green H2", "fossilccoal":"Coking coal", "fossilpci":"PCI coal","co2 transport and storage": "CO2 transport\n& storage"}

    #first, plot colorerd layer
    axes[0].bar(x_pos, sub_df_LCO_merge["cost"], color = sub_df_LCO_merge["color_type"],  edgecolor = "grey")

    #then, transparent stacked bars
    for i, comp in enumerate(["capex", "other costs", "elec", "fossilng", "h2", "fossilccoal", "fossilpci", "co2 transport and storage"]):

        column = sub_df_LCO_merge[comp].fillna(0)

        axes[0].bar(x_pos, column, bottom = height, edgecolor = "dimgrey", color = color[i], alpha = alpha_list[i])

        annot_height = height + column/2
        height += column
        
        #here, add any annotation needed
        if column[0] > 0:
            axes[0].hlines(annot_height[0], 0.4, 0.55, colors = "darkgrey", linewidth = 1)
            if comp != "elec":
                axes[0].text(x=0.6,y= annot_height[0], s=labels[comp], verticalalignment='center', c= "grey")
            else:
                axes[0].text(x=0.6, y= annot_height[0]-20, s=labels[comp], verticalalignment='center', c= "grey")

        if column[1] > 0:
            if comp != "elec":
                if comp != "co2 transport and storage":
                    axes[0].text(x=3.6,y= annot_height[1], s=labels[comp], verticalalignment='center', c= "grey")
                    axes[0].hlines(annot_height[1], 3.4, 3.55, colors = "darkgrey", linewidth = 1)
                else:
                    axes[0].annotate(labels[comp],(3.4, annot_height[1]), xytext = (3.6, annot_height[1]+20),c= "grey",
                                     arrowprops=dict(color='darkgrey', width = 0.05, headwidth = 0))
                    #texts.append(axes[0].text(x=3.6,y= annot_height[2]+20, s=labels[comp]))
            else:
                axes[0].text(x=3.6,y= annot_height[1]-20, s=labels[comp], verticalalignment='center', c= "grey")
                axes[0].hlines(annot_height[1], 3.4, 3.55, colors = "darkgrey", linewidth = 1)

        if column[5] > 0:
            axes[0].hlines(annot_height[5], 10.9, 11.05, colors = "darkgrey", linewidth = 1)
            if comp != "elec":
                axes[0].text(x=11.1,y= annot_height[5], s=labels[comp], verticalalignment='center', c= "grey")
            else:
                axes[0].text(x=11.1,y= annot_height[5]-20, s=labels[comp], verticalalignment='center', c= "grey")
        
    #add annotation to xaxis

    # axes[0].annotate('', xy=(5.2, -100),xytext=(11.2,-100),       
    #             arrowprops=dict(arrowstyle='-',facecolor='black', linestyle = "--"),
    #             annotation_clip=False)

    axes[0].annotate('H2-DRI-EAF, for different H2 costs',xy=(8.25,-120),xytext=(8.25,-120), color = "black", horizontalalignment = "center",
                annotation_clip=False)

    #other plot settings
    axes[0].set_xticks(x_pos, sub_df_LCO_merge["code"])
    
    axes[0] = change_spines(axes[0])
    
    axes[0].set_title("Levelized cost comparison based on different H2 cost assumptions", fontweight="bold",loc = "left")
    axes[0].set_ylabel(f"Levelized cost \n(EUR{unit})")



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
    axes[1].set_ylabel(f"Fuel-switching CO2 price \n(EUR/tCO2)")
    axes[1].set_xlabel(f"Hydrogen cost (EUR/MWh)")
    axes[1].set_ylim(0, 255)
    axes[1].set_xlim(0, 255)
    # axes[1].legend([(s1,l1), (s2,l2)],["DRI-EAF replacing BF-BOF steel","BF-BOF-CCS replacing BF-BOF steel"], loc = "lower right")
    axes[1].legend([(s1,l1), (s2,l2), (l3)],["H2-DRI-EAF replacing BF-BOF steel","BF-BOF-CCS replacing BF-BOF steel", "H2 cost at which BF-BOF-CCS and H2-DRI-EAF\n have the same abatement cost"], loc = "lower right")

    fig.tight_layout()
    plt.show()

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
    sub_df_LCO_breakdown = sub_df_LCO_breakdown.drop_duplicates("LCO").dropna(axis=1, how='all').reset_index(drop = True).apply(pd.to_numeric, errors='ignore').round(2)
    sub_df_LCO_breakdown.rename(columns = {"LCO": "cost"}, inplace = True)
    sub_df_LCO_breakdown.drop(["tech"], axis =1, inplace = True)
    selected_comps = [ "cost", "capex","ch3oh_capex", "opex", "ch3oh_opex","elec","ch3oh_elec","ch3oh_heat", "h2","ch3oh_h2","ch3oh_co2" ]
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

    fig, axes = plt.subplots(nrows = 1,ncols=1, figsize=(11,10))

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

        column = sub_df_LCO_merge[comp].fillna(0)

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

    axes.annotate('E-jet fuel, for different H2 and CO2 costs',xy=(8.25,-120),xytext=(8.25,-120), color = "black", horizontalalignment = "center",
                annotation_clip=False)

    #other plot settings
    axes.set_xticks(x_pos, sub_df_LCO_merge["code"])
    
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
    plt.show()

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

    sub_df_FSCP_nocomp = dfs[(dfs["sector"]==sector) & (dfs["type"]==type) ]
    sub_df_FSCP2_nocomp = dfs[(dfs["sector"]==sector) & (dfs["type"]=="ccs") ]
    sub_df_FSCP3_nocomp = dfs_retrofit[(dfs_retrofit["sector"]==sector) & (dfs_retrofit["type"]=="ccs") ]


    fscp_color = np.unique(sub_df_FSCP["color_type"])[0]
    fscp_color2 = np.unique(sub_df_FSCP2["color_type"])[0]
    fscp_color3 = "#46bfeb"

    
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
    sub_df_LCO_merge.loc[sub_df_LCO["type"]=="comp", "code"] = "DACCS compensation of\nresidual emissions" 
    sub_df_LCO_merge.sort_values(by = ["em", sensitivity], ascending = [False, True], inplace=True)

    fig = plt.figure(figsize=(12,10), layout = "constrained")
    axes = fig.subplot_mosaic(
        """
        AABB
        CCC.
        """
    )

    # make specific filtered dfs for different combinations of mitigation options
    sub_df_LCO_merge_CCS = sub_df_LCO_merge[(sub_df_LCO_merge["type"]=="ccs") |(sub_df_LCO_merge["type"]=="ccsretrofit") | (sub_df_LCO_merge["type"]=="comp") ]
    
    sub_df_LCO_merge_CCS['em_abated'] = sub_df_LCO_merge_CCS.apply(calculate_em_abated, args=(fossil_em, sub_df_LCO_merge_CCS), axis=1)
    sub_df_LCO_merge_CCS["annot"] = ["New plant", "Retrofit", np.nan]

    #first, plot colorerd layer
    facecolors = sub_df_LCO_merge_CCS["color_type"].apply(lambda color: hex_to_rgba(color, 0.1))
    edgecolors = sub_df_LCO_merge_CCS["color_type"].apply(lambda color: hex_to_rgba(color, 1))
    bars = axes["A"].bar([0,0,1], sub_df_LCO_merge_CCS["fscp"], color = facecolors, edgecolor = edgecolors, width = sub_df_LCO_merge_CCS["em_abated"])

    # #other plot settings
    # axes["A"].set_xticks([0,0,1], sub_df_LCO_merge_CCS["code"])
    
    # Set the x-ticks to the right side of the bars
    xticks = [bar.get_x() + bar.get_width() for bar in bars[1:]]
    axes["A"].set_xticks(xticks)

    # Set the x-tick labels to the 'code' values
    cumulative_em_abated = sub_df_LCO_merge_CCS["em_abated"].unique().cumsum().round(2)
    cumulative_em_abated = (np.rint(np.array(cumulative_em_abated *100 / cumulative_em_abated.max()))).astype(int)
    axes["A"].set_xticklabels(cumulative_em_abated)

    # Add 'code' values under the bars
    for bar, code in zip(bars, sub_df_LCO_merge_CCS["code"]):
        axes["A"].text(bar.get_x()+0.01 , 5, code, ha='left', va='bottom', rotation = 90)

    axes["A"] = change_spines(axes["A"])

    for i, (fscp, annot) in enumerate(zip(sub_df_LCO_merge_CCS["fscp"], sub_df_LCO_merge_CCS["annot"])):
        if pd.isna(annot):
            continue
        axes["A"].text(0, fscp, annot, ha='center', va='bottom', color = "grey")

    axes["A"].set_title("Marginal abatement cost curve for BF-BOF-CCS\nand DACCS combination, for a retrofit and a\nnew plant case.", fontweight="bold",loc = "left")
    axes["A"].set_ylabel(f"Fuel-switching CO2 price\n(EUR/tCO2)")
    axes["A"].set_xlabel(f"% emissions mitigation compared to BF-BOF (w/o CCS)")
    
    sub_df_LCO_merge_h2 = sub_df_LCO_merge[(sub_df_LCO_merge["type"]=="h2") | (sub_df_LCO_merge["type"]=="comp") ]
    sub_df_LCO_merge_h2['em_abated'] = sub_df_LCO_merge_h2.apply(calculate_em_abated, args=(fossil_em, sub_df_LCO_merge_h2), axis=1)
    
    #first, plot colorerd layer
    facecolors = sub_df_LCO_merge_h2["color_type"].apply(lambda color: hex_to_rgba(color, 0.1))
    edgecolors = sub_df_LCO_merge_h2["color_type"].apply(lambda color: hex_to_rgba(color, 1))

    bars = axes["B"].bar([0,0,0,0,1], sub_df_LCO_merge_h2["fscp"], color=facecolors, edgecolor=edgecolors, width=sub_df_LCO_merge_h2["em_abated"])
    
    #axes["B"].bar([0,0,0,0,1], sub_df_LCO_merge_h2["fscp"], color = sub_df_LCO_merge_h2["color_type"],   alpha = 0.2,edgecolor = sub_df_LCO_merge_h2["color_type"], width = sub_df_LCO_merge_h2["em_abated"])
    ##other plot settings
    #axes["B"].set_xticks([0,1], sub_df_LCO_merge_h2["code"].unique())
    
    # Set the x-ticks to the right side of the bars
    xticks = [bar.get_x() + bar.get_width() for bar in bars[3:]]
    axes["B"].set_xticks(xticks)

    # Set the x-tick labels to the 'code' values
    cumulative_em_abated = sub_df_LCO_merge_h2["em_abated"].unique().cumsum().round(2)
    cumulative_em_abated = (np.rint(np.array(cumulative_em_abated *100 / cumulative_em_abated.max()))).astype(int)
    axes["B"].set_xticklabels(cumulative_em_abated)

    # Add 'code' values under the bars
    for i, (bar, code) in enumerate(zip(bars[3:], sub_df_LCO_merge_h2["code"][3:])):
        if i == 1:
            axes["B"].text(bar.get_x()+0.01, 5, code, ha='left', va='bottom', rotation = 90)
        else:
            axes["B"].text(bar.get_x()+0.01 , 5, code, ha='left', va='bottom', rotation = 90)
    # bar.get_x() + bar.get_width() / 2
            
    axes["B"] = change_spines(axes["B"])

    for i, (fscp, annot) in enumerate(zip(sub_df_LCO_merge_h2["fscp"], sub_df_LCO_merge_h2["annot"])):
        if pd.isna(annot):
            continue
        axes["B"].text(0, fscp, annot, ha='center', va='bottom', color = "grey")

    axes["B"].set_title("Marginal abatement cost curve for H2-DRI-EAF\nand DACCS combination, with different H2\ncost assumptions", fontweight="bold",loc = "left")
    axes["B"].set_ylabel(f"Fuel-switching CO2 price\n(EUR/tCO2)")
    axes["B"].set_xlabel(f"% emissions mitigation compared to BF-BOF (w/o CCS)")

    #now, FSCP figure
    FSCP = axes["C"]
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


    # ## extra vline on bottom pannel at intersection- not sure if needed
    # FSCP.vlines(intersection, 0,250,ls="--", color = "darkgrey", lw = 1)
    # #dummy line for legend
    # ldashed = Line2D([0], [0], color='darkgrey', linewidth=1, linestyle='--')
    # # Get current xticks and xticklabels
    # xticks = list(FSCP.get_xticks())
    # xticklabels = list(FSCP.get_xticklabels())

    # # Add intersection to xticks and its label to xticklabels
    # xticks.append(intersection)
    # xticklabels.append(f'{intersection:.0f}')

    # # Set new xticks and xticklabels
    # FSCP.set_xticks(xticks)
    # FSCP.set_xticklabels(xticklabels)

    # # Change color of last tick label to grey
    # for label in FSCP.get_xticklabels():
    #     if f'{intersection:.0f}' == label.get_text(): 
    #         label.set_color('darkgrey')


    FSCP = change_spines(FSCP)
    
    FSCP.set_title("FSCP dependency on assumed H2 cost", fontweight="bold", loc ="left")
    FSCP.set_ylabel(f"Fuel-switching CO2 price \n(EUR/tCO2)")
    FSCP.set_xlabel(f"Hydrogen cost (EUR/MWh)")
    FSCP.set_ylim(0, 255)
    FSCP.set_xlim(0, 255)
    
    # Get the current position of the subplot
    box = FSCP.get_position()

    # Adjust the position of the subplot
    # The values are in fractions of the figure width and height
    FSCP.set_position([box.x0, box.y0, box.width * 0.7, box.height])
    FSCP.legend([(l1), (l2), (l3), (l4), (l5), (l6)],
                ["H2-DRI-EAF + DACCS \n(full mitigation)",
                 "BF-BOF-CCS + DACCS \n(full mitigation, new plant)",
                 "BF-BOF-CCS + DACCS \n(full mitigation, retrofit)",
                 "H2-DRI-EAF \n(incomplete mitigation)",
                 "BF-BOF-CCS \n(incomplete mitigation, new plant)",
                 "BF-BOF-CCS \n(incomplete mitigation, retrofit)"],
                bbox_to_anchor=(1, 0.05), loc="lower left", borderaxespad=0,
                # bbox_to_anchor=(0.84, 0.05), loc="lower left", borderaxespad=0,
                ncol = 1)

    fig.tight_layout()
    plt.show()
    