import numpy as np
import pandas as pd
import json
from pathlib import Path
from src.calc import calc_costs
from src.plot import common

# remove annoying warning that is irrelevant here
pd.options.mode.chained_assignment = None  # default='warn'

# colors and units for the plotting
color_dict_tech = common.color_dict_tech
color_dict_series = pd.Series(color_dict_tech)


def diff_fscp(lst):
    lst = np.array(lst)
    num_negative_values = np.sum(lst < 0)

    if lst.size == 1 or num_negative_values >= 1:
        return 1000

    if np.unique(lst).size == 1:
        return 0

    # Use numpy's partition function to find the smallest and second smallest values
    lst_partitioned = np.partition(lst, 1)

    return lst_partitioned[1] - lst_partitioned[0]

def lowest_fscp(lst):
    arr = np.array(lst)
    non_negative_arr = arr[arr >= 0]
    
    if non_negative_arr.size == 0:  # If there are only negative values, fscp not well defined => we return the whole array
        return arr
    else:
        # min_non_negative = non_negative_arr.min()
        # arr[arr >= 0] = min_non_negative
        min = arr.min()
        arr[arr != 0] = min

    return arr


def lowest_value(lst):
    """
    Only used for when the df has a negative fscp. In this case, we want to select the technology with the lowest cost.
    """
    if len(lst) == 1:
        return lst
    else:
        return min(lst)

def get_lowest_fscp(df):
    """
    Returns a DataFrame with the lowest fscp for each sector
    """
    # drop rows with NaN values
    df = df.dropna()

    # Filter rows with the lowest FSCP by sector
    lowest_fscp_mask = df.groupby(["sector"])["fscp"].transform(lowest_fscp) == df["fscp"]
    df = df[lowest_fscp_mask]

    # Filter rows with the lowest cost (only applies to rows with negative FSCPs)
    lowest_cost_mask = df.groupby(["sector"])["cost"].transform(lowest_value) == df["cost"]
    df = df[lowest_cost_mask]

    # Filter rows with the lowest emission (only applies to rows with negative FSCPs, that have the same cost)
    lowest_emission_mask = df.groupby(["sector"])["em"].transform(lowest_value) == df["em"]
    df = df[lowest_emission_mask]

    #if there are still duplicates (same cost and emission), choose one at random
    if len(df) != 5:
        df = df.drop_duplicates(subset=["fscp"], keep="first")

    return(df)

def retrofit_params(retrofit_techs):
    """
    Returns a dictionary with the new retrofit CAPEX for the given technologies.
    This is always calculated relative to the fossil reference.
    If retrofit_techs is None, the default parameters are returned.
    
    Parameters:
    retrofit_techs (list): The technologies to retrofit.

    Returns:
    new_params (dict): The retrofit CAPEX parameters.
    """
    new_params = dict()
    # Navigate to the sibling directory and file
    file_path = str(Path(__file__).parent / '../src/calc/params.json')

    # Open and read the JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)

    if retrofit_techs is not None:
        # Store all the fossil techs' capex values in a dictionary
        fossil_capexs = {tech['key']: tech.get('capex') for tech in data['techs'] if 'fossil' in tech['key']}

        for tech in data["techs"]:
            if tech.get('key') in retrofit_techs:
                sector_to_retrofit = tech.get('key').split("_")[1]
                fossil_entry = f'fossil_{sector_to_retrofit}'
                #get the correct fossil capex for the sector, using the dictionnary built previously
                new_params[tech.get('key')+"_capex"] = round(tech.get("capex") - fossil_capexs.get(fossil_entry, 0), 1)
                new_params[fossil_entry+"_capex"] = 0

    return new_params

def ccu_possible(df, big_df):
    """
    Checks whether there is an uptaker AND a producer of CCU in the given DataFrame.
    If there is disagreement on CCU, the FSCP of the CCU lines in big_df is set to 
    a large amount (as it should tend to infinity mathematically).
    
    Parameters:
    df (pd.DataFrame): The DataFrame to check.
    big_df (pd.DataFrame): The DataFrame to update.

    Returns:
    bool: True if CCU is possible, False otherwise.
    pd.DataFrame: The updated DataFrame.
    """
    ccu_mask = df["type"].str.contains('ccu')
    if ccu_mask.any():
        sector_mask1 = df["sector"].str.contains('chem|plane|ship')
        sector_mask2 = df["sector"].str.contains('steel|cement')
        if sector_mask1[ccu_mask].any() and sector_mask2[ccu_mask].any():
            return True, big_df
        else:
            ccu_mask_big_df = big_df["type"].str.contains('ccu')
            big_df.loc[ccu_mask_big_df, "fscp"] = 100000
            return False, big_df
    else:
        #case where there is no ccu as best option in this df
        return True, big_df

def get_df(scenario = None, DACCS = True, CCU_coupling = False, compensate = False, retrofit = False, retrofit_techs = None, load_json = True, **kwargs):
    # run the technoeconomic calculation
    if retrofit and retrofit_techs is None:
        raise ValueError("If retrofit is True, retrofit_techs cannot be None. Please provide a list of technologies to retrofit.")

    if retrofit:
        new_capex_kwargs = retrofit_params(retrofit_techs = retrofit_techs)
        kwargs.update(new_capex_kwargs)

    inexistant_techs_ifNODACCS=[
        "ccs_plane",
        "h2_plane",
        "ccs_ship",
        "efuel_steel",
        "ccs_chem",
        "h2_chem",
        "efuel_cement",
        "h2_cement",
        "comp_plane",
        "comp_ship",
        "comp_chem",
        "comp_steel",
        "comp_cement",
    ]

    #define calc_LCO args
    calc_all_LCO_args = {
        "ccu_income": CCU_coupling,
        "compensate_residual_ems": compensate,
        "load_json": load_json,
        **kwargs
    }

    # Only add the inexistant_techs argument if necessary
    if not DACCS:
        calc_all_LCO_args["inexistant_techs"] = inexistant_techs_ifNODACCS

    # Call calc_all_LCO
    df_total = calc_costs.calc_all_LCO(**calc_all_LCO_args)

    # overall data frame
    df_total.reset_index(inplace=True, drop=True)

    # extract cost of h2 for the plot
    h2_cost = df_total.loc[df_total["tech"] == "h2", "cost"].iat[0]
    df_total["h2"] = h2_cost

    # filter only for the sectors we are interested in
    df_data = df_total[df_total["tech"].str.contains("plane|ship|steel|chem|cement")]

    # split tech name into type (ccs, ccu, ..) and actual sector
    df_data[["type", "sector"]] = df_data["tech"].str.split(pat="_", n=1, expand=True)

    df_data.sort_values(by=["sector", "type"], ascending=[True, False], inplace=True)

    df_data.replace(-1, np.nan, inplace=True)


    #The code below is faster than the previous (shorter) method of using groupby + apply with the calc_FSCP function.
    
    # Create a separate DataFrame with only the 'fossil' rows and select only necessary columns
    fossil_df = df_data[df_data["type"] == "fossil"][["sector", "cost", "em", "elec"]]

    # Merge the original DataFrame with the 'fossil' DataFrame and specify new col names
    df_macc = df_data.merge(fossil_df, on="sector", suffixes=("", "_fossil"))

    # Now you can calculate the FSCP directly without using groupby or apply
    df_macc["fscp"] = calc_costs.FSCP(df_macc["cost"], df_macc["em"], df_macc["cost_fossil"], df_macc["em_fossil"])
    df_macc["elec_fscp"] = calc_costs.FSCP(df_macc["elec"], df_macc["em"], df_macc["elec_fossil"], df_macc["em_fossil"])
    df_macc["co2_comp"] = df_macc["co2_comp"] * 100 / df_macc["em_fossil"]

    df_temp = get_lowest_fscp(df_macc)

    # Create a boolean mask that selects the rows you want
    mask = ~df_macc.index.isin(df_temp.index)

    if CCU_coupling:
        # Removes any shading arising from CCU
        mask &= df_macc["type"] != "ccu"
        
    df_temp_secondbest = get_lowest_fscp(df_macc[mask])

    # Then, need to check whether CCU_coupling is on. 
    if CCU_coupling:
        ccu_possible_result = ccu_possible(df_temp, df_macc)
        # If CCU not possible, use the new df_macc_ccu_filtered.
        if not ccu_possible_result[0]:
            df_macc_ccufiltered = ccu_possible_result[1]
            df_temp = get_lowest_fscp(df_macc_ccufiltered)

            # Update the mask
            mask = ~df_macc_ccufiltered.index.isin(df_temp.index)
            mask &= df_macc_ccufiltered["type"] != "ccu"
            df_temp_secondbest = get_lowest_fscp(df_macc_ccufiltered[mask])

    #here calculate difference between temp and tempsecondbest
    df_temp["delta_fscp"] = pd.concat([df_temp, df_temp_secondbest]).groupby("sector", group_keys=False)[
        "fscp"
    ].transform(diff_fscp)

    # add color column
    df_temp["color_type"] = df_temp["type"].map(color_dict_series)

    if scenario is not None:
        df_temp["scenario"] = scenario

    return df_temp
