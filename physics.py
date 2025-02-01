import math

gravitational_constant = 6.67430 * 10 ** -11  # m^3 kg^-1 s^-2
earth_mass = 5.972 * 10 ** 24  # kg
earth_radius = 6400000  # m, simplified
# sutton-graves
k = 1.7415e-4  # kg^0.5/m
sigma = 5.67e-8  # W/m^2K^4


class Physics:
    @staticmethod
    def gravitational_acceleration(height):
        return gravitational_constant * earth_mass / ((earth_radius + height) ** 2)

    @staticmethod
    def atmospheric_density(height):
        return 1.2 * math.e ** (-1.244268 * (10 ** -4) * height)

    @staticmethod
    def acceleration_in_dir_of_flight(thrust, state, effective_area, sim):
        T = thrust * math.cos(state.a)  # in the direction of the flight
        D = Physics.atmospheric_density(state.h) * (state.v ** 2) * effective_area * 0.5
        Fg = state.m * Physics.gravitational_acceleration(state.h) * math.sin(state.gamma)
        sim.loss_drag += D / state.m * sim.time_step
        sim.loss_gravity += Fg / state.m * sim.time_step
        sim.deltaV += T / state.m * sim.time_step
        return (T - D - Fg) / state.m

    @staticmethod
    def nose_heat_flux(temperature, velocity, height, effective_radius, emmisivity=.8):
        # sutton-graves
        heat_flux_in = k * (velocity ** 3) * math.sqrt(Physics.atmospheric_density(height) / effective_radius)
        heat_flux_out = emmisivity * sigma * ((temperature ** 4) - (293 ** 4))
        return max(0, heat_flux_in - heat_flux_out)

    @staticmethod
    def max_temperature(velocity, height, effective_radius, emmisivity=.8):
        return (k / (emmisivity * sigma) * (velocity ** 3) * math.sqrt(
            Physics.atmospheric_density(height) / effective_radius) + 293 ** 4) ** (1 / 4)

    @staticmethod
    def angular_velocity(thrust, state):
        T = thrust * math.sin(state.a)  # perpendicular to the flight direction
        c = (-Physics.gravitational_acceleration(state.h) + (state.v ** 2) / (earth_radius + state.h))
        return (math.cos(state.gamma) * c + T / state.m) / state.v