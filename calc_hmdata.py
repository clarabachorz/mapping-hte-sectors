import multiprocessing as mp
import numpy as np
import itertools
import pandas as pd
from pathlib import Path

from tools import process_tech_df


def mainfig_params():
    param_dict = {
        "h2_LCO": np.arange(0, 242, 2),  # used to be 2
        "co2_LCO": np.arange(0, 1225, 25),  # used to be 25
        "co2ts_LCO": [15],    
    }

    params = itertools.product(*param_dict.values())
    return (param_dict, params)

def sup_params():
    param_dict = {
        "h2_LCO": np.arange(0, 242, 2),  # used to be 2
        "co2_LCO": np.arange(0, 1225, 25),  # used to be 25
        "co2ts_LCO": [8, 30, 100,200],
    }
    params = itertools.product(*param_dict.values())
    return (param_dict, params)

def mainfig_calc_dfs(param_set, param_dict):
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    df_normal = process_tech_df.get_df(scenario = "normal", load_json = load_json, **temp_dict)
    df_ccu = process_tech_df.get_df(scenario = "ccu", CCU_coupling=True, DACCS = True, compensate=False, load_json= load_json, **temp_dict)
    df_comp = process_tech_df.get_df(scenario = "comp", CCU_coupling=True, DACCS=False, compensate=True, load_json=load_json, **temp_dict)

    return [df_normal, df_ccu, df_comp]

def sup_calc_dfs(param_set, param_dict):
    temp_dict = dict(zip(param_dict.keys(), param_set))
    df = process_tech_df.get_df(**temp_dict)
    return df

def sup2_calc_dfs(param_set, param_dict):
    temp_dict = dict(zip(param_dict.keys(), param_set))
    retrofitted_techs = ["ccs_steel", "ccu_steel", "comp_steel", "ccs_cement", "ccu_cement", "comp_cement", "comp_chem"] 

    df_greenfield = process_tech_df.get_df(scenario = "greenfield", **temp_dict)
    df_brownfield = process_tech_df.get_df(scenario="brownfield", retrofit=True, retrofit_techs = retrofitted_techs, **temp_dict)
    df_greenfieldcomp = process_tech_df.get_df(scenario = "greenfield_comp", compensate=True, **temp_dict)
    df_brownfieldcomp = process_tech_df.get_df(scenario="brownfield_comp", compensate=True, retrofit=True, retrofit_techs = retrofitted_techs, **temp_dict)

    return [df_greenfield, df_brownfield, df_greenfieldcomp, df_brownfieldcomp]

def sup3_calc_dfs(param_set, param_dict):
    #bfccs sensitivity (+/- 50% on CCS capex)
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    df_normal = process_tech_df.get_df(scenario = "normal", load_json = load_json, **temp_dict)
    df_lowCCS = process_tech_df.get_df(scenario = "lowCCS", load_json = load_json,ccs_steel_capex = 782.5, **temp_dict)
    df_highCCS = process_tech_df.get_df(scenario = "highCCS", load_json = load_json,ccs_steel_capex = 978.7, **temp_dict)
    df_normalcomp = process_tech_df.get_df(scenario = "normal_comp", DACCS=False, compensate=True, load_json = load_json, **temp_dict)
    df_lowCCScomp = process_tech_df.get_df(scenario = "lowCCS_comp", DACCS=False, compensate=True, load_json = load_json,ccs_steel_capex = 782.5, **temp_dict)
    df_highCCScomp = process_tech_df.get_df(scenario = "highCCS_comp", DACCS=False, compensate=True, load_json = load_json,ccs_steel_capex = 978.7, **temp_dict)
    

    return [df_normal, df_lowCCS, df_highCCS, df_normalcomp, df_lowCCScomp, df_highCCScomp]

def save_mainfigdata(mainfig_list_of_dfs):
    list_of_dfs = [df for sublist in mainfig_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/mainfig_rawdata.csv'))

def save_supdata(sup_list_of_dfs):
    df_final = pd.concat(sup_list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/sup_rawdata.csv'))

def save_sup2data(sup2_list_of_dfs):
    list_of_dfs = [df for sublist in sup2_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/supretrofit_rawdata.csv'))

def save_sup3data(sup3_list_of_dfs):
    list_of_dfs = [df for sublist in sup3_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/supBFCCS_rawdata.csv'))

if __name__ == "__main__":
    # calculates data for 3 heatmap figures: the main figure, supplementary figure with CO2 transport and storage sensitivity,
    # and supplementary with retrofit sensitivity
    
    #multiprocessing to speed up hm data calculation
    with mp.Pool(mp.cpu_count()) as pool:
        mainfig_list_of_dfs = pool.starmap(mainfig_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup_list_of_dfs = pool.starmap(sup_calc_dfs, [(param_set, sup_params()[0]) for param_set in sup_params()[1]])
        sup2_list_of_dfs = pool.starmap(sup2_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup3_list_of_dfs = pool.starmap(sup3_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])

    save_mainfigdata(mainfig_list_of_dfs)
    save_supdata(sup_list_of_dfs)
    save_sup2data(sup2_list_of_dfs)
    save_sup3data(sup3_list_of_dfs)


