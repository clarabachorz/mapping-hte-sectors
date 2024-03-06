from typing import Dict, Set, Any
from src.calc.TechData import TechData

class Tech:
    """
    A class used to represent a Technology.

    ...

    Attributes
    ----------
    common_dict : dict
        a dictionary that stores common data for all instances of the class
    init_dict : dict
        a dictionary that stores initial data for the instance
    LCO_comps : dict
        a dictionary that stores the components making up the LCOP (Levelized Cost of a Product)
    feedstock_demand : dict
        a dictionary that stores the feedstock demand for the instance
        eg. Methanol (CH3OH) requires electricity, H2 and CO2
    allowed_attr : set
        a set that stores the allowed attributes for the instance. If a user inputs anything outside this set in the init_dict, an error will be raised
    wacc : float
        Weighted Average Cost of Capital, default is 0.1
    flh : float
        Full Load Hours, default is 0.9
    lifetime : int
        Lifetime of the technology in years, default is 20

    Methods
    -------
    """

    COMMON_DICT: Dict = {}
    SECTORS = ['chem','plane','ship','cement','steel']

    def __init__(self, init_dict, comp = False, ccu_income = False):
        """
        Constructs all the necessary attributes for the Tech object.

        Parameters
        ----------
            init_dict : dict
                The initial data for the instance.
            comp : bool, optional
                A flag indicating if the instance is has full compensation of emissions activated (default is False).
            ccu_income : bool, optional
                A flag indicating if the instance has Carbon Capture and Utilization income (default is False).
        """

        self.init_dict = init_dict
        self.LCO_comps = {}
        self.feedstock_demand = {}
        # define some default values for LCO calculations, in case user does not explicitely define them
        self.wacc = 0.1
        self.flh = 0.9
        self.lifetime = 20

        self.allowed_attr = set(
            {
                "key",
                "unit",
                "desc",
                "LCO",
                "capex",
                "opex",
                "othercosts",
                "flh",
                "wacc",
                "lifetime",
                "co2em",
                "co2capt",
                "compensation",
                "recycledco2",
                "offgrid",
                "co2ccusupply",
                "co2ccuincome"
            }
        )

        self.set_attr()
        
        self.check_offgrid()
        self.check_comp(comp)
        self.check_ccuincome(ccu_income)

        self.append_dict()
    
    # def update(self, new_dict, comp, ccu_income):
    #     self.update_dict(new_dict)
    #     #need to delete the previously calculated LCO, to be able to update it. Otherwise, if the tech already has a
    #     # defined LCO, this is automatically taken.
    #     delattr(self, "LCO")

    #     self.set_attr()
        
    #     self.check_offgrid()
    #     self.check_comp(comp)
    #     self.check_ccuincome(ccu_income)

    #     self.append_dict()
        
    # def update_dict(self, new_dict):
    #     self.init_dict = new_dict

    def get_dict(self) -> dict:
        """Returns a dictionnary storing cost, emission and electricity usage data for all technologies."""
        return {k: v.get_vals() for k, v in self.COMMON_DICT.items()}

    def append_dict(self) -> None:
        """Calculates all the components associated with the technology and appends them to the COMMON_DICT."""
        self.LCO_comps["tech"] = self.key
        self.COMMON_DICT[self.key] = TechData(
            self.get_LCO(),
            self.get_eff_em(),
            self.get_eff_elec(),
            self.desc,
            self.get_total_co2dem(),
            self.get_total_em() -self.get_eff_em()
        )
    
    def set_attr(self):
        """Sets the attributes of the instance using the init_dict."""
        for k, v in self.init_dict.items():
            if k in self.allowed_attr:
                self.add_attr(k, v)
            elif "demand" in k:
                self.add_feedstock_cost(k, v)
            else:
                raise KeyError(
                    f'key "{k}" is not in expected list of attributes: {self.allowed_attr}'
                )
                
    def add_attr(self, k, v) -> None:
        """Adds an attribute to the instance"""
        setattr(self, k, v)
        
    def add_feedstock_cost(self, k, v) -> None:
        """Adds a feedstock demand to the feedstock dict."""
        x = k.index("demand")
        self.feedstock_demand[k[:x]] = v

    def check_offgrid(self) -> None:
        """Checks if the technology is offgrid, and if so, changes the electricity demand to elecoffgrid."""
        if getattr(self, "offgrid", False):
            self.feedstock_demand["elecoffgrid"] = self.feedstock_demand.pop("elec")

    def check_comp(self, comp: bool) -> None:
        if comp and any(sector in self.key for sector in self.SECTORS) and not "fossil" in self.key:
            self.compensation = True

    def check_ccuincome(self, ccu_income: bool) -> None:
        if ccu_income and any(sector in self.key for sector in self.SECTORS) and not "fossil" in self.key:    
            self.co2ccuincome = True

    def get_LCO(self):
        """Calculates the Levelized Cost of a Product (LCO) for the technology, only if it hasn't already been set externally."""
        if not hasattr(self, "LCO"):
            self.LCO=(
                self.LCOX_wo_energy()
                + self.get_other_costs()
                + self.get_total_feedstock_costs()
                + self.get_carbon_tax()
                + self.get_co2_storage_cost()
                + self.get_comp_cost()
                + self.get_ccu_income()
            )
        self.LCO_comps["LCO"] = self.LCO
        return self.LCO

#amke into property ? and change the name to eff_em ?
    def get_eff_em(self):
        """Calculates the effective emissions of the technology, taking into account the compensation flag."""
        if getattr(self, "compensation", False):
            if getattr(self, "offgrid", False):
                raise Exception("Compensation and offgrid electricity at the same time are not supported by current code version")
            return self.get_eff_elec() * self.COMMON_DICT["elec"].em
        return self.get_total_em()

#make into property ? and change the name to eff_elec ?
    def get_eff_elec(self):
        """Calculates the effective electricity demand of the technology, taking into account the compensation flag.
        If compensation is on, the effective electricity demand is the sum of the tech electricity demand and DAC electricity demand,
        calculated using total emissions * electricity demand to compensate a ton of CO2"""
        if getattr(self, "compensation", False):
            return self.get_total_elec() + (self.get_total_em() * self.COMMON_DICT["co2"].elec)
        return self.get_total_elec()

    @property
    def anf(self) -> float:
        """Calculates the annuity factor, which is used to annualize the capex."""
        return ((self.wacc * (1 + self.wacc) ** self.lifetime) / ((1 + self.wacc) ** self.lifetime - 1))

    def LCOX_wo_energy(self) -> float:
        """Calculates the LCO without the energy component. This is the sum of the annualized capex and fixed opex, divided by the full load hours."""
        try:
            ann_capex = self.capex * self.anf
        except AttributeError:
            ann_capex = 0
        
        try:
            fix_opex = self.opex * self.capex / 100
        except AttributeError:
            fix_opex = 0
        
        LCO_noenergy = (ann_capex + fix_opex) / self.flh
        
        self.LCO_comps["capex"] = ann_capex / self.flh
        self.LCO_comps["opex"] = fix_opex / self.flh

        return LCO_noenergy

    def get_total_feedstock_costs(self):
        """Calculates and returns the total feedstock costs associated with the tech"""
        return sum(self.get_feedstock_cost(key) for key in self.feedstock_demand.keys())
    
    def get_total_em(self) -> float:
        """Calculates and returns total CO2 emissions associated with the tech
        Includes direct CO2 emissions, indirect CO2 emissions from feedstocks, 
        minus the CO2 captured, the CO2 from CCU, and the CO2 from feedstock recycling. """
        total_em = self.get_em() - self.get_co2_capt() - self.get_co2_ccu() - self.get_noncombustedplastic_co2()
        total_em += sum(self.get_feedstock_em(key) for key in self.feedstock_demand.keys()) 
        return total_em
    
    def get_total_elec(self) -> float:
        """Calculates and returns total electricity demand associated with the tech
        by adding the direct elec demand, and the feedstocks elec demand."""
        total_elecdem = self.feedstock_demand.get("elec", 0)
        total_elecdem += sum(self.get_elec_dem(key) for key in self.feedstock_demand.keys())
        return total_elecdem
        
    def get_total_co2dem(self) -> float:
        total_co2dem = self.get_co2dem()
        total_co2dem += sum(self.get_feedstock_co2dem(key) for key in self.feedstock_demand.keys())
        return(total_co2dem)

    def get_carbon_tax(self) -> float:
        """Returns the cost component of the carbon tax for the tech, or 0 if not defined."""
        if getattr(self, "compensation", False):
            return 0
        try:
            self.LCO_comps["co2 tax"] = self.get_total_em() * self.COMMON_DICT["co2tax"].LCO
            return self.LCO_comps["co2 tax"]
        except:
            return 0
    
    def get_co2_storage_cost(self) -> float:
        """Returns the cost of CO2 storage for the tech, or 0 if not defined."""
        try:
            self.LCO_comps["co2 transport and storage"] = self.co2capt * self.COMMON_DICT["co2ts"].LCO
            return self.LCO_comps["co2 transport and storage"]
        except:
            return 0

    def get_comp_cost(self) -> float:
        """Returns the cost of compensating for CO2 emissions for the tech, or 0 if not defined.
        The cost is the sum of DAC (CO2 capture) and CO2 transport and storage costs."""
        if getattr(self, "compensation", False):
            self.LCO_comps["co2"] = self.get_total_em() * getattr(self.COMMON_DICT["co2"], "LCO", 0)
            self.LCO_comps["co2 transport and storage"] = self.get_total_em() * getattr(self.COMMON_DICT["co2ts"], "LCO", 0)
            return self.LCO_comps["co2"] + self.LCO_comps["co2 transport and storage"]
        return(0)

        
    def get_ccu_income(self) -> float:
        """Returns the income from Carbon Capture and Utilization (CCU), or 0 if not defined.
        Only if CO2 from CCU is priced."""
        if not getattr(self, "co2ccuincome", False):
            return 0
        return -getattr(self, "co2ccusupply", 0) * self.COMMON_DICT["co2ccu"].LCO

    def get_other_costs(self) -> float:
        """Returns the other costs of the tech, or 0 if not defined.
        Other costs is usually a fixed OPEX, or other costs that are not defined in the variables above."""
        self.LCO_comps["other costs"] = getattr(self, 'othercosts', 0)
        return self.LCO_comps["other costs"]

    def get_em(self) -> float:
        """Returns the CO2 emissions of the tech, or 0 if not defined."""
        return getattr(self, "co2em", 0)

    def get_co2_capt(self) -> float:
        """Returns the amount of CO2 captured by the tech, or 0 if not defined."""
        return getattr(self, "co2capt", 0)

    def get_co2_ccu(self) -> float:
        """ Only for sectors that provide CO2 from CCU (where co2ccusupply is defined)
        Calculates the amount of CO2 from CCU that is taken in charge by the user, and substract it from the total emissions.
        This is done using the attribution, which is between 0 and 1, and is defined by the co2ccu_em variable."""
        try:
            return self.co2ccusupply * self.COMMON_DICT["co2ccu"].em
        except:
            return 0

    def get_co2dem(self) -> float:
        """Returns the DAC demand, in tCO2/unit of the tech, or 0 if not defined."""
        return self.feedstock_demand.get("co2", 0)
    
    def get_feedstock_cost(self, key) -> float:
        """Obtains the LCO cost component of the feedstock "key" (feedstock demand * feedstock cost).
        If the feedstock "key" is not used for this tech, returns 0."""
        try:
            self.LCO_comps[key] = self.feedstock_demand[key] * self.COMMON_DICT[key].LCO
            return self.LCO_comps[key]
        except:
            return 0

    def get_feedstock_em(self, key) -> float:
        """Obtains the CO2 emissions of the feedstock "key" (feedstock demand * feedstock emissions)."""
        try:
            return self.feedstock_demand[key] * self.COMMON_DICT[key].em
        except:
            return 0
    
    def get_elec_dem(self, key) -> float:
        """Obtains the electricity demand of the feedstock "key" (feedstock demand * feedstock electricity demand)."""
        if key in ["elec", "elecoffgrid"]:
            return self.feedstock_demand.get(key, 0) * 1
        else:
            try:
                return self.feedstock_demand[key] * self.COMMON_DICT[key].elec
            except:
                return 0
    
    def get_feedstock_co2dem(self, key) -> float:
        """Obtains the CO2 demand of the feedstock "key" (feedstock demand * feedstock CO2 demand)."""
        try:
            return self.feedstock_demand[key] * self.COMMON_DICT[key].total_co2dem
        except:
            return 0         

    def get_noncombustedplastic_co2(self) -> float:
        """Returns the CO2 emissions saved from recycled plastics, or 0 if not defined."""
        return getattr(self, "recycledco2", 0)
