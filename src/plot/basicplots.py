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

def plot_basicfigs():
    # Code starts here

    # calculate the df with default co2 and h2 LCOs
    df_macc, LCO_comps_default = get_LCOs(calc_LCO_comps=True) 

    #then, calculate the LCO breakdown for the LCO_comps_default df
    # the function isolates the total contributions of h2 and co2 to each row of the df
    df_macc_wLCObreakdown = get_LCOcontributions(df_macc, LCO_comps_default)

    # h2 parameters for the bar plots
    h2_costs = [50, 100, 150, 200] #in EUR/MWh
    h2_costs_aviationfig = [25,50,75,100]
    h2_costs_steel = [100,  200] #in EUR/MWh

    # co2 parameters for the bar plots
    co2_costs = [300, 300, 300, 300] #in EUR/tonne CO2
    co2_costs_fuels = [200, 400, 600, 800] #in EUR/tonne CO2
    co2_costs_steel = [350, 350, 350, 350]

    co2_transport_storage_costs = 15 #in EUR/tonne CO2

    LCOs_df = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs,calc_LCO_comps=True) for h2, co2 in zip(h2_costs, co2_costs)]
    LCOs_df_breakdown = pd.concat([calc_costs.breakdown_LCO_comps(LCO_df[1])[0] for LCO_df in LCOs_df])
    
    LCOs_df_aviation = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, calc_LCO_comps=True) for h2, co2 in zip(h2_costs_aviationfig, co2_costs)]

    LCOs_fuels_df = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, calc_LCO_comps=True) for h2, co2 in zip(h2_costs, co2_costs_fuels)]

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
    LCOs_df_ccu = [get_LCOs(h2_cost=70, co2_cost=800, co2_transport_storage=co2_transport_storage_costs, co2ccu_co2em = attr, calc_LCO_comps=False) for attr in [0.5,0.6,0.7,0.8,0.9]]

    #calculate LCOs for different gas prices
    LCOs_df_blueh2 = [get_LCOs(h2_cost=70, co2_cost=800, co2_transport_storage=co2_transport_storage_costs, fossilng_LCO = fossilng_LCO, calc_LCO_comps=False) for fossilng_LCO in [10,20,30,40]]
    
    ### UNCOMMENT BELOW TO DO SOME PLOTTING (FIGURE 1)###

    # line below: full panel plotting, with no MAC, but instead LCO breakdown
    common.plot_large_panel(
        df_macc_wLCObreakdown,
    )

    common.plot_barplotfscp(
        pd.concat([LCO_df[0] for LCO_df in LCOs_df]),
        LCOs_df_breakdown,
        sector="steel",
    )

    common.plot_barplotaviation(
        LCOs_df_aviation[0][0],
        pd.concat([calc_costs.breakdown_LCO_comps(LCO_df[1])[0] for LCO_df in LCOs_df_aviation]),
        h2costs=h2_costs_aviationfig,
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

