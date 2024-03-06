class TechData:
    def __init__(self, LCO, eff_em, eff_elec, desc, total_co2dem, total_em_eff_em):
        self.LCO = LCO
        self.em = eff_em
        self.elec = eff_elec
        self.desc = desc
        self.total_co2dem = total_co2dem
        self.co2_comp = total_em_eff_em

    def __str__(self):
        return self.desc
    
    def get_vals(self):
        return ([self.LCO, self.em, self.elec, self.desc, self.total_co2dem, self.co2_comp])