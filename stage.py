class Stage:
    structure_mass = 0 # in tons
    propellant_mass = 0 # in tons
    specific_impulse = 0 # in m/s
    propellant_mass_flux = 0 # in kg/s
    payload_mass = 0 # in tons
    burn_time = 0 # in s
    thrust = 0 # in N

    def __init__(self, structure_mass, propellant_mass, specific_impulse, propellant_mass_flux, payload_mass):
        self.structure_mass = structure_mass
        self.propellant_mass = propellant_mass
        self.specific_impulse = specific_impulse
        self.propellant_mass_flux = propellant_mass_flux
        self.payload_mass = payload_mass
        self.burn_time = propellant_mass * 1000 / propellant_mass_flux
        self.thrust = specific_impulse * propellant_mass_flux

    def mass_at_time(self, time):
        # result in kg
        start_mass = self.structure_mass * 1000 + self.payload_mass * 1000 + self.propellant_mass * 1000
        return start_mass - self.propellant_mass_flux * time
