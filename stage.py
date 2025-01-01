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

    def update(self):
        self.burn_time = self.propellant_mass * 1000 / self.propellant_mass_flux
        self.thrust = self.specific_impulse * self.propellant_mass_flux

    def mass_at_time(self, time):
        # result in kg
        start_mass = self.structure_mass * 1000 + self.payload_mass * 1000 + self.propellant_mass * 1000
        return start_mass - self.propellant_mass_flux * time


def optimize_staging_two_stages(stages, structure_index, payload, iterations=100):
    total_mass = sum(stage.structure_mass + stage.payload_mass + stage.propellant_mass for stage in stages)
    stage0 = stages[0]
    stage1 = stages[1]
    stage1.structure_mass -= (payload - stage1.payload_mass) * structure_index
    stage1.propellant_mass -= (payload - stage1.payload_mass) * (1 - structure_index)
    stage1.payload_mass = payload
    total_structure = sum(stage.structure_mass for stage in stages)
    increment = total_structure / iterations

    smallest_delta = 1000000
    best_i = 0

    for i in range(iterations):
        stage0.structure_mass = total_structure - increment * i
        stage1.structure_mass = increment * i
        stage0.propellant_mass = stage0.structure_mass * 10
        stage1.propellant_mass = stage1.structure_mass * 10

        stage0_ratio = total_mass / (total_mass-stage0.propellant_mass)
        stage1_ratio = (total_mass - stage0.propellant_mass - stage0.structure_mass) / (stage1.structure_mass + payload)

        delta = abs(stage0_ratio - stage1_ratio)
        if delta < smallest_delta:
            smallest_delta = delta
            best_i = i
        else:
            break

    stage0.structure_mass = total_structure - increment * best_i
    stage1.structure_mass = increment * best_i
    stage0.propellant_mass = stage0.structure_mass * 10
    stage1.propellant_mass = stage1.structure_mass * 10
    stage0.update()
    stage1.update()

    return [stage0, stage1]