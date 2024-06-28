import numpy as np
import pandas as pd
import json
import re
import math
from pathlib import Path

from src.calc.tech_class import Tech

#define a global variable to store the last read json file data
last_read_data = None

def calc_all_LCO(
    path_to_params=str(Path(__file__).parent / 'params.json'),
    compensate_residual_ems=False,
    ccu_income=False,
    inexistant_techs=None,
    load_json = True,
    **kwargs
):
    global last_read_data

    if inexistant_techs is None:
        inexistant_techs = [
            "ccs_plane",
            "h2_plane",
            "ccs_ship",
            "efuel_steel",
            "ccs_chem",
            "h2_chem",
            "efuel_cement",
            "h2_cement",
        ]

    user_params = kwargs
    Tech.COMMON_DICT = {}
    final_dict = {}

    # json file holds external assumptions, which are then updated by user inputs through kwargs
    # to make to code faster, it is preferable to not load the json file every time, and instead use the last read data
    # instead, the user can input their own parameter changes through the kwargs argument
    if load_json:
        with open(path_to_params) as f:
            data = json.load(f)
            last_read_data = data
    else:
        data = last_read_data

    # initialise the techs using the assumptions from the json file
    for row in data["techs"]:
        temp_dict = {
            k.rsplit("_", 1)[1]: v
            for k, v in user_params.items()
            if k.rsplit("_", 1)[0] == row["key"]
        }
        row.update(temp_dict)
        temp_tech = Tech(row, comp=compensate_residual_ems, ccu_income=ccu_income)

        final_dict.update(temp_tech.get_dict())
    
    ## add an empty entry for technologies that don't exist (inexistant_techs)
    for i in inexistant_techs:
        type = i.split("_")[0]

        if type == "h2":
            type = "h2/nh3"

        final_dict[i] = [np.nan, np.nan, np.nan, "No " + type+" option", np.nan, np.nan]
    #function below takes roughly 1/2 or 1/3 of total task time
    df = to_df_fmt(final_dict)
    
    for key in user_params.keys():
        df[key] = user_params[key]

    return df


def calc_all_LCO_wbreakdown(
    #path_to_params="./analysis/common/params.json",
    path_to_params=str(Path(__file__).parent / 'params.json'),
    compensate_residual_ems=False,
    ccu_income=False,
    inexistant_techs=None,
    load_json = True,
    **kwargs
):
    global last_read_data

    if inexistant_techs is None:
        inexistant_techs = [
            "ccs_plane",
            "h2_plane",
            "ccs_ship",
            "efuel_steel",
            "ccs_chem",
            "h2_chem",
            "efuel_cement",
            "h2_cement",
        ]

    user_params = kwargs
    Tech.COMMON_DICT = {}
    final_dict = {}
    rows_LCO_comps = []

    # json file holds external assumptions, which are then updated by user inputs through kwargs
    # to make to code faster, it is preferable to not load the json file every time, and instead use the last read data
    # instead, the user can input their own parameter changes through the kwargs argument
    if load_json:
        with open(path_to_params) as f:
            data = json.load(f)
            last_read_data = data
    else:
        data = last_read_data

    # initialise the techs using the assumptions from the json file
    for row in data["techs"]:
        temp_dict = {
            k.rsplit("_", 1)[1]: v
            for k, v in user_params.items()
            if k.rsplit("_", 1)[0] == row["key"]
        }
        row.update(temp_dict)
        temp_tech = Tech(row, comp=compensate_residual_ems, ccu_income=ccu_income)

        # to get the individual LCO components
        rows_LCO_comps.append(temp_tech.LCO_comps)

        final_dict.update(temp_tech.get_dict())
    
    ## add an empty entry for technologies that don't exist (inexistant_techs)
    for i in inexistant_techs:
        type = i.split("_")[0]

        if type == "h2":
            type = "h2/nh3"

        final_dict[i] = [np.nan, np.nan, np.nan, "No " + type+" option", np.nan, np.nan]
    #function below takes roughly 1/2 or 1/3 of total task time
    df = to_df_fmt(final_dict)
    
    for key in user_params.keys():
        df[key] = user_params[key]

    return (df, pd.DataFrame(rows_LCO_comps))


def to_df_fmt(dict):
    rows = [[key] + value for key, value in dict.items()]

    df = pd.DataFrame(
        rows, columns=["tech", "cost", "em", "elec", "code", "co2", "co2_comp"]
    ).round(6)
    return df


def FSCP(green_cost, green_emission, fossil_cost, fossil_emission):
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(fossil_emission > green_emission, 
                          (green_cost - fossil_cost) / (fossil_emission - green_emission), 
                          np.nan)
        return np.round(result, 5)

def calc_FSCP(df):
    # identify the fossil tech row, extract row as dict
    fossil_row = df.loc[df["type"] == "fossil"].to_dict("records")[0]

    # calculate the FSCP
    df["fscp"] = FSCP(df["cost"], df["em"], fossil_row["cost"], fossil_row["em"])
    df["elec_fscp"] = FSCP(df["elec"], df["em"], fossil_row["elec"], fossil_row["em"])
    df["co2_comp"] = df["co2_comp"] * 100 / fossil_row["em"]

    return df

#currently only used for python interface. Change in the future
#duplicate of breakdown_LCO_comps below
def calc_LCO_breakdown(h2_cost=70, co2_cost=300, co2ts_cost=15):
    _, LCO_components = calc_all_LCO_wbreakdown(
        get_LCO_comps=True,
        h2_LCO=h2_cost,
        co2_LCO=co2_cost,
        co2ts_LCO=co2ts_cost,
    )
    LCO_components.replace(0.0, np.nan, inplace=True)

    new_LCO_rows = []
    LCO_components.apply(process_LCO_rows, axis=1, args=(LCO_components, new_LCO_rows))
    updated_LCO = update_LCO_components(LCO_components, new_LCO_rows)

    sectors_LCO, fuel_LCO = split_LCO_df(updated_LCO)
    return sectors_LCO, fuel_LCO

def breakdown_LCO_comps(LCO_components):
    #this function takes the LCO components and breaks them down into their subcomponents
    # eg. for an e-fuel plane flying on e-jet fuel, breaksdown the cost of e-jet fuel
    # into the cost of the electricity, the cost of the h2, the cost of the co2, etc.
    LCO_components.replace(0.0, np.nan, inplace=True)

    new_LCO_rows = []
    LCO_components.apply(process_LCO_rows, axis=1, args=(LCO_components, new_LCO_rows))
    updated_LCO = update_LCO_components(LCO_components, new_LCO_rows)

    sectors_LCO, fuel_LCO = split_LCO_df(updated_LCO)
    return sectors_LCO, fuel_LCO

def process_LCO_rows(current_row, LCO_component_rows, new_LCO_rows):
    # breaks up current row into its components and updates the LCO components

    current_row = current_row.convert_dtypes().dropna()
    tech_name = current_row["tech"]

    if re.search("ship|steel|plane|chem|cement|fossil", tech_name):
        # here, filter and select only the fuel rows - ignore ship, steel, etc
        return

    for _, other_row in LCO_component_rows.iterrows():
        other_tech_name = other_row["tech"]
        if current_row.name == other_row.name or math.isnan(
            other_row.get(tech_name, np.nan)
        ):
            # make sure we're not multiplying h2 row by h2 row
            # and check that tech_name is included in other_row AND is not nan
            continue

        param_fraction = other_row[tech_name] / current_row["LCO"]
        # Removes tech,LCO entry and multiply
        new_row = current_row.drop(["tech", "LCO"]).multiply(param_fraction)

        # obtain list of tech with which rows have already been updated,
        # see if some of them intersect with the new row
        # if so, a second update with these results is needed
        updated_params = [row["tech"] for row in new_LCO_rows]
        common_subparams = list(set(new_row.keys()).intersection(updated_params))

        for subparam in common_subparams:
            # update the subparams with the "updated_params"
            # choose the first row that matches the subparam
            updated_subparam = next(
                row for row in new_LCO_rows if row["tech"] == subparam
            )

            subparam_fraction = new_row[subparam] / updated_subparam["LCO"]

            # Removes tech,LCO entry and clean up
            new_subrow = updated_subparam.drop(["tech", "LCO"]).multiply(
                subparam_fraction
            )

            # rename the new row for clarity
            new_subrow = new_subrow.add_prefix(subparam + "_")
            # add results to the row we are working with
            new_row = pd.concat([new_row, new_subrow])

        new_row = new_row.add_prefix(tech_name + "_")
        new_row = pd.concat([other_row, new_row])

        if other_tech_name not in updated_params:
            # check whether the entry already exists in the new rows list.
            new_LCO_rows.append(new_row)
        else:
            for idx, item in enumerate(new_LCO_rows):
                if other_tech_name == item["tech"]:
                    new_row = item.combine_first(new_row)
                    new_LCO_rows[idx] = new_row

def update_LCO_components(old_LCO_components, new_LCO_components):
    old_LCO_components.set_index("tech", inplace=True)
    new_LCO_components = (
        pd.concat(new_LCO_components, axis=1).transpose().set_index("tech")
    )
    # merge: updated_LCO now contains all the details we want !
    updated_LCO_components = new_LCO_components.combine_first(
        old_LCO_components
    ).dropna(axis=1, how="all")
    return updated_LCO_components

def split_LCO_df(LCO_components):
    # separate the df into sectors and fuel
    sectors_LCO = (
        LCO_components[
            LCO_components.index.str.contains("plane|ship|cement|chem|steel")
        ]
        .dropna(axis=1, how="all")
        .reset_index()
    )
    fuel_LCO = (
        LCO_components[
            ~LCO_components.index.str.contains("plane|ship|cement|chem|steel")
        ]
        .dropna(axis=1, how="all")
        .reset_index()
    )

    return sectors_LCO, fuel_LCO
