import pandas as pd
from src.plot import common
from src.calc import calc_costs
from tools import process_tech_df

# Define constants, default assumptions for these parameters
H2_COST = 70
CO2_COST = 300
CO2_TRANSPORT_STORAGE = 15

def load_IEA_data(file_paths):
    dataframes = []
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        df = df[df["category"] == "cat3_energy"]
        df = df[["subsector.y", "value_cat"]]
        dataframes.append(df)
    return dataframes

def get_LCOcontributions(df, LCO_comps):
    # Get the breakdown for the sectors (index 0) and reset the index to get the tech name
    detailed_LCO = calc_costs.breakdown_LCO_comps(LCO_comps)[0].set_index("tech")

    # use the regex to filter column with co2 and h2 contributions, and sum them
    LCO_h2_contribution = detailed_LCO.filter(regex="^(h2|.*_h2$)$").sum(axis=1)
    LCO_co2_contribution = detailed_LCO.filter(regex="^(co2|.*_co2$)$").sum(axis=1)

    # concatenating the dataframes to get the final dataframe
    costs_breakdown = pd.concat(
        [
            LCO_co2_contribution,
            LCO_h2_contribution,
            detailed_LCO["LCO"],
        ],
        axis=1,
        keys=["co2_cost", "h2_cost", "lco"],
    )
    with pd.option_context("future.no_silent_downcasting", True):
        costs_breakdown = costs_breakdown.fillna(0).infer_objects(copy=False)

    # calculate LCO without co2 and h2 costs
    costs_breakdown["lco_noh2co2"] = costs_breakdown["lco"] - (costs_breakdown["co2_cost"] + costs_breakdown["h2_cost"])

    # Merge with main df, df_macc
    merged_df = pd.merge(df, costs_breakdown, on="tech", how="left").drop("lco", axis=1)
    return merged_df

def get_LCOs(
    h2_cost=H2_COST, co2_cost=CO2_COST, co2_transport_storage=CO2_TRANSPORT_STORAGE, calc_LCO_comps=False, compensate = False, **kwargs,
):
    # run the technoeconomic calculation
    if not calc_LCO_comps:
        df_data = calc_costs.calc_all_LCO(
            elec_co2em=0,
            h2_LCO=h2_cost,
            co2_LCO=co2_cost,
            co2ts_LCO=co2_transport_storage,
            co2tax_othercosts=0,
            compensate_residual_ems=compensate,
            **kwargs,
        )
    else:
        df_data, LCO_comps = calc_costs.calc_all_LCO_wbreakdown(
            elec_co2em=0,
            h2_LCO=h2_cost,
            co2_LCO=co2_cost,
            co2ts_LCO=co2_transport_storage,
            co2tax_othercosts=0,
            compensate_residual_ems=compensate,
            **kwargs,
        )

    # split tech name into type (ccs, ccu, ..) and actual sector
    df_data[["type", "sector"]] = df_data["tech"].str.split("_", expand=True)

    #all fuel rows in this df have sector = None. Separate them out
    df_fuels = df_data[df_data["sector"].isnull()]

    # groups the dataframe by sector, and calculates all FSCPs.
    df_macc = df_data.groupby("sector", as_index=False, group_keys=False).apply(
        lambda x: calc_costs.calc_FSCP(x)
    )

    #reassemble the dataframe to include the fuel rows
    df_macc = pd.concat([df_macc, df_fuels])

    if calc_LCO_comps:
        return (df_macc, LCO_comps)
    else:
        return df_macc

    
    

def get_LCOs_kerosene_project():
    df = pd.read_csv("h2LCOkerosene.csv")

    #list to stock values
    kerosene_lco_average = []
    kerosene_lco_high = []
    kerosene_lco_low = []

    kerosene_lcobreakdown_average = []
    kerosene_lcobreakdown_high = []
    kerosene_lcobreakdown_low = []
    #CAPEX: cost in USD/kW * extra for stack replacement * conversion to EUR * conversion to /MWh
    #test, comps = calc_costs.calc_all_LCO_wbreakdown(elec_LCO = 60, h2_capex = 1850*1.5*0.92/8.76, h2_flh = 3750/8760, h2_elecdemand = 1/0.65, co2_LCO = 200)
    
    #iteration
    for index, row in df.iterrows():
        params_average = {
            'elec_LCO': row['elec_LCO_average'],
            'h2_capex': row['h2_capex_average'],
            'h2_flh': row['h2_flh_average'],
            'h2_elecdemand': row['h2_elecdemand_average'],
            'co2_LCO': row['co2_LCO_average'],
            'ch3oh_capex': row['ch3oh_capex_average'],
            'MtJ_capex': row['MtJ_capex_average'],
        }
        params_high = {
            'elec_LCO': row['elec_LCO_high'],
            'h2_capex': row['h2_capex_high'],
            'h2_flh': row['h2_flh_high'],
            'h2_elecdemand': row['h2_elecdemand_high'],
            'co2_LCO': row['co2_LCO_high'],
            'ch3oh_capex': row['ch3oh_capex_high'],
            'MtJ_capex': row['MtJ_capex_high'],
        }
        params_low = {
            'elec_LCO': row['elec_LCO_low'],
            'h2_capex': row['h2_capex_low'],
            'h2_flh': row['h2_flh_low'],
            'h2_elecdemand': row['h2_elecdemand_low'],
            'co2_LCO': row['co2_LCO_low'],
            'ch3oh_capex': row['ch3oh_capex_low'],
            'MtJ_capex': row['MtJ_capex_low'],
        }

        # Calculate LCOs for each scenario
        lco_average, lcobreakdown_average = calc_costs.calc_all_LCO_wbreakdown(**params_average)
        lco_high, lcobreakdown_high = calc_costs.calc_all_LCO_wbreakdown(**params_high)
        lco_low, lcobreakdown_low = calc_costs.calc_all_LCO_wbreakdown(**params_low)


        #calculate extended breakdown
        lcobreakdown_average = calc_costs.breakdown_LCO_comps(lcobreakdown_average)[1]
        lcobreakdown_average['Year'] = row['year']
        lcobreakdown_average['case'] = 'medium'

        lcobreakdown_high = calc_costs.breakdown_LCO_comps(lcobreakdown_high)[1]
        lcobreakdown_high['Year'] = row['year']
        lcobreakdown_high['case'] = 'high'
        
        lcobreakdown_low = calc_costs.breakdown_LCO_comps(lcobreakdown_low)[1]
        lcobreakdown_low['Year'] = row['year']
        lcobreakdown_low['case'] = 'low'

        kerosene_lcobreakdown_average.append(lcobreakdown_average.loc[lcobreakdown_average["tech"] == "MtJ"].dropna(axis = 1).drop(columns=["tech", "ch3oh", "ch3oh_h2", "h2"]))
        kerosene_lcobreakdown_high.append(lcobreakdown_high.loc[lcobreakdown_high["tech"] == "MtJ"].dropna(axis = 1).drop(columns=["tech", "ch3oh", "ch3oh_h2", "h2"]))
        kerosene_lcobreakdown_low.append(lcobreakdown_low.loc[lcobreakdown_low["tech"] == "MtJ"].dropna(axis = 1).drop(columns=["tech", "ch3oh", "ch3oh_h2", "h2"]))

    # concatenate all cases into a single DataFrame
    breakdown_df_average = pd.concat(kerosene_lcobreakdown_average, ignore_index=True)
    breakdown_df_high = pd.concat(kerosene_lcobreakdown_high, ignore_index=True)
    breakdown_df_low = pd.concat(kerosene_lcobreakdown_low, ignore_index=True)


    df_tosave = pd.concat([breakdown_df_average, breakdown_df_high, breakdown_df_low], ignore_index=True)
    # #rename some columns
    df_tosave = df_tosave.rename(columns={"capex": "MtJ_capex","opex": "MtJ_opex","elec": "MtJ_elec", "h2_capex":"MtJ_h2_capex", "h2_elec":"MtJ_h2_elec", "h2_opex":"MtJ_h2_opex"})
    print(df_tosave)
    # # #save df

    df_tosave.to_csv("keroseneLCO_only.csv", index=False)

def plot_basicfigs():
    # Code starts here

    # calculate the df with default co2 and h2 LCOs
    df_macc, LCO_comps_default = get_LCOs(calc_LCO_comps=True) 

    #then, calculate the LCO breakdown for the LCO_comps_default df
    # the function isolates the total contributions of h2 and co2 to each row of the df
    df_macc_wLCObreakdown = get_LCOcontributions(df_macc, LCO_comps_default)

    # h2 parameters for the bar plots
    h2_costs = [50, 100, 150, 200] #in EUR/MWh
    h2_costs_aviationfig = [50,100,150]
    h2_costs_steel = [100,  200] #in EUR/MWh
    h2_costs_fuels = [231.6, 139.6, 109.9, 80.2] #in EUR/MWh

    # co2 parameters for the bar plots
    co2_costs = [300, 300, 300, 300] #in EUR/tonne CO2
    co2_costs_fuels = [200, 200, 200, 200] #in EUR/tonne CO2
    co2_costs_steel = [350, 350, 350, 350]

    co2_transport_storage_costs = 15 #in EUR/tonne CO2
    co2_ts_costs = [15,50,100]

    LCOs_df = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs,calc_LCO_comps=True) for h2, co2 in zip(h2_costs, co2_costs)]
    LCOs_df_breakdown = pd.concat([calc_costs.breakdown_LCO_comps(LCO_df[1])[0] for LCO_df in LCOs_df])

    #used in the steel barplot levelized cost +fscp figure. BF-BOF-CCS capex changed by +/- 50%. CCS is not sensitive to H2 or CO2 costs.
    LCOs_df_steelccshigh = get_LCOs(h2_cost=100, co2_cost=100, co2_transport_storage=co2_transport_storage_costs, ccs_steel_capex = 978.7, calc_LCO_comps=False)
    LCOs_df_steelccslow = get_LCOs(h2_cost=100, co2_cost=100, co2_transport_storage=co2_transport_storage_costs, ccs_steel_capex = 782.5, calc_LCO_comps=False) 
    
    LCOs_df_aviation = [get_LCOs(h2_cost=h2, co2_cost=300, co2_transport_storage=co2_ts_costs, calc_LCO_comps=True) for h2, co2_ts_costs in zip(h2_costs_aviationfig, co2_ts_costs)]

    LCOs_fuels_df = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, calc_LCO_comps=True) for h2, co2 in zip(h2_costs_fuels, co2_costs_fuels)]

    #additional set of LCOs for steel FSCP figure
    LCOs_df_base = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, fossil_steel_capex = 0, comp_steel_capex = 0) for h2, co2 in zip(h2_costs_steel, co2_costs_steel)]
    #calculate comp LCOS
    LCOs_df_comp = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, compensate=True,fossil_steel_capex = 0, comp_steel_capex = 0) for h2, co2 in zip(h2_costs_steel, co2_costs_steel)]
    #calculate retrofit args
    new_kwargs = process_tech_df.retrofit_params(["ccs_steel"])
    # calculate retrofit LCOs, AND comp+retrofit LCOs
    LCOs_df_retrofit = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, compensate=False, **new_kwargs) for h2, co2 in zip(h2_costs_steel, co2_costs_steel)]
    LCOs_df_comp_retrofit = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, compensate=True, **new_kwargs) for h2, co2 in zip(h2_costs_steel, co2_costs_steel)]

    #calculate LCOs for different attributions (CCU)
    LCOs_df_ccu = [get_LCOs(h2_cost=50, co2_cost=800, co2_transport_storage=co2_transport_storage_costs, co2ccu_co2em = attr, calc_LCO_comps=False) for attr in [0.5,0.6,0.7,0.8]]

    #calculate LCOs for different gas prices
    LCOs_df_blueh2 = [get_LCOs(h2_cost=70, co2_cost=800, co2_transport_storage=co2_transport_storage_costs, fossilng_LCO = fossilng_LCO, calc_LCO_comps=False) for fossilng_LCO in [10,20,30,40]]
    

    get_LCOs_kerosene_project()
    ### UNCOMMENT BELOW TO DO SOME PLOTTING (FIGURE 1)###

    # line below: full panel plotting, with no MAC, but instead LCO breakdown
    common.plot_large_panel(
        df_macc_wLCObreakdown,
    )

    common.plot_barplotfscp(
        pd.concat([LCO_df[0] for LCO_df in LCOs_df]),
        LCOs_df_breakdown,
        [LCOs_df_steelccslow, LCOs_df_steelccshigh],
        sector="steel",
    )

    common.plot_barplotaviation(
        LCOs_df_aviation[0][0],
        pd.concat([calc_costs.breakdown_LCO_comps(LCO_df[1])[0] for LCO_df in LCOs_df_aviation]),
        h2costs=h2_costs_aviationfig,
        co2ts_costs=co2_ts_costs,
    )

    common.plot_barplotfuels(
        pd.concat([LCO_fuel_df[0] for LCO_fuel_df in LCOs_fuels_df]),
        pd.concat([calc_costs.breakdown_LCO_comps(LCO_fuel_df[1])[1] for LCO_fuel_df in LCOs_fuels_df]),
    )

    common.plot_steel_macc(
        pd.concat([LCO_df for LCO_df in LCOs_df_base]),
        pd.concat([LCO_df for LCO_df in LCOs_df_retrofit]),
        pd.concat([LCO_df for LCO_df in LCOs_df_comp]),
        pd.concat([LCO_df for LCO_df in LCOs_df_comp_retrofit]),
        sector="steel",
    )

    common.plot_large_panel_ccuattr(LCOs_df_ccu)

    common.blueh2_costanalysis(LCOs_df_blueh2)

    common.nonfossilco2_supplycurve()

