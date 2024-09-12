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

def sup4_calc_dfs(param_set, param_dict):
    #aviation fossil cost sensitivity (varying fossil kerosene cost)
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    df_normal = process_tech_df.get_df(scenario = "normal", load_json = load_json, **temp_dict)
    df_lowfossilJ = process_tech_df.get_df(scenario = "lowfossilJ", load_json = load_json,fossilJ_LCO = 25, **temp_dict)
    df_highfossilJ = process_tech_df.get_df(scenario = "highfossilJ", load_json = load_json,fossilJ_LCO = 75, **temp_dict)
    

    return [df_normal, df_lowfossilJ, df_highfossilJ]

def sup5_calc_dfs(param_set, param_dict):
    #blue hydrogen sensitivity (add technologies)
    #and add blue steel emissions based on methane leakage
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    inexistant_techs = [
            "ccs_plane",
            "h2_plane",
            "ccs_ship",
            "efuel_steel",
            "ccs_chem",
            "h2_chem",
            "efuel_cement",
            "h2_cement"
        ]
    #calculate methane emissions for blue h2 depending on leakage
    GWP100 = 34 #CO2 equivalent
    GWP20 = 86 #CO2 equivalent
    NG_lhv = 13.1 #kWh/kg or MWh/ton

    #calculate extra cost from 0.1% leakage:
    low_leakage_emgwp100 = 0.001*(1/NG_lhv)*GWP100
    high_leakage_emgwp100 = 0.03*(1/NG_lhv)*GWP100
    low_leakage_emgwp20 = 0.001*(1/NG_lhv)*GWP20
    high_leakage_emgwp20 = 0.03*(1/NG_lhv)*GWP20

    df_normal = process_tech_df.get_df(scenario = "noleakage", load_json = load_json, inexistant_techs = inexistant_techs, blueh2_co2em = 0, **temp_dict)
    df_lowleakage = process_tech_df.get_df(scenario = "lowleakage", load_json = load_json,inexistant_techs = inexistant_techs, blueh2_co2em = low_leakage_emgwp100, **temp_dict)
    df_highleakage = process_tech_df.get_df(scenario = "highleakage", load_json = load_json,inexistant_techs = inexistant_techs,blueh2_co2em = high_leakage_emgwp100, **temp_dict)
    df_normalcomp = process_tech_df.get_df(scenario = "noleakage_compgwp100", load_json = load_json, compensate=True, inexistant_techs = inexistant_techs, blueh2_co2em = 0, **temp_dict)
    df_lowleakagecomp = process_tech_df.get_df(scenario = "lowleakage_compgwp100", load_json = load_json, compensate=True,inexistant_techs = inexistant_techs,blueh2_co2em = low_leakage_emgwp100, **temp_dict)
    df_highleakagecomp = process_tech_df.get_df(scenario = "highleakage_compgwp100", load_json = load_json, compensate=True,inexistant_techs = inexistant_techs,blueh2_co2em = high_leakage_emgwp100, **temp_dict)
    df_normalcomp20 = process_tech_df.get_df(scenario = "noleakage_compgwp20", load_json = load_json, compensate=True, inexistant_techs = inexistant_techs, blueh2_co2em = 0, **temp_dict)
    df_lowleakagecomp20 = process_tech_df.get_df(scenario = "lowleakage_compgwp20", load_json = load_json, compensate=True,inexistant_techs = inexistant_techs,blueh2_co2em = low_leakage_emgwp20, **temp_dict)
    df_highleakagecomp20 = process_tech_df.get_df(scenario = "highleakage_compgwp20", load_json = load_json, compensate=True,inexistant_techs = inexistant_techs,blueh2_co2em = high_leakage_emgwp20, **temp_dict)
    

    return [df_normal, df_lowleakage, df_highleakage, df_normalcomp, df_lowleakagecomp, df_highleakagecomp, df_normalcomp20, df_lowleakagecomp20, df_highleakagecomp20]

def sup6_calc_dfs(param_set, param_dict):
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    df_normal = process_tech_df.get_df(scenario = "normal", load_json = load_json, co2ccu_co2em = 0.85, **temp_dict)
    df_ccu = process_tech_df.get_df(scenario = "ccu", CCU_coupling=True, DACCS = True, compensate=False, load_json= load_json, co2ccu_co2em = 0.85, **temp_dict)
    df_comp = process_tech_df.get_df(scenario = "comp", CCU_coupling=True, DACCS=False, compensate=True, load_json=load_json, co2ccu_co2em = 0.85, **temp_dict)

    return [df_normal, df_ccu, df_comp]

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

def save_sup4data(sub4_list_of_dfs):
    list_of_dfs = [df for sublist in sub4_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/supfossilcost_rawdata.csv'))

def save_sup5data(sub5_list_of_dfs):
    list_of_dfs = [df for sublist in sub5_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/supblueh2_rawdata.csv'))

def save_sup6data(sub6_list_of_dfs):
    list_of_dfs = [df for sublist in sub6_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)
    df_final.to_csv(str(Path(__file__).parent / 'data/supCCUattrib_rawdata.csv'))

if __name__ == "__main__":
    # calculates data for 3 heatmap figures: the main figure, supplementary figure with CO2 transport and storage sensitivity,
    # and supplementary with retrofit sensitivity
    
    #multiprocessing to speed up hm data calculation
    with mp.Pool(mp.cpu_count()) as pool:
        mainfig_list_of_dfs = pool.starmap(mainfig_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup_list_of_dfs = pool.starmap(sup_calc_dfs, [(param_set, sup_params()[0]) for param_set in sup_params()[1]])
        sup2_list_of_dfs = pool.starmap(sup2_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup3_list_of_dfs = pool.starmap(sup3_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup4_list_of_dfs = pool.starmap(sup4_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup5_list_of_dfs = pool.starmap(sup5_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])
        sup6_list_of_dfs = pool.starmap(sup6_calc_dfs, [(param_set, mainfig_params()[0]) for param_set in mainfig_params()[1]])

    save_mainfigdata(mainfig_list_of_dfs)
    save_supdata(sup_list_of_dfs)
    save_sup2data(sup2_list_of_dfs)
    save_sup3data(sup3_list_of_dfs)
    save_sup4data(sup4_list_of_dfs)
    save_sup5data(sup5_list_of_dfs)
    save_sup6data(sup6_list_of_dfs)


