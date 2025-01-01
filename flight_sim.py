import math
from orbit import Orbit

gravitational_constant = 6.67430 * 10 ** -11  # m^3 kg^-1 s^-2
earth_mass = 5.972 * 10 ** 24  # kg
earth_radius = 6371000  # m
effective_area = 15  # m^2
effective_nose_radius = 0.5 # m
# sutton-graves
k = 1.7415e-4 # kg^0.5/m
sigma = 5.67e-8 # W/m^2K^4


def gravitational_acceleration(height):
    return gravitational_constant * earth_mass / ((earth_radius + height) ** 2)


def atmospheric_density(height):
    return 1.2 * math.e ** (-1.244268 * (10 ** -4) * height)


def acceleration_in_dir_of_flight(thrust, velocity, mass, height, a, gamma, sim):
    T = thrust * math.cos(a)  # in the direction of the flight
    D = atmospheric_density(height) * (velocity ** 2) * effective_area * 0.5
    Fg = mass * gravitational_acceleration(height) * math.sin(gamma)
    sim.loss_drag += D / mass * sim.time_step
    sim.loss_gravity += Fg / mass * sim.time_step
    sim.deltaV += T / mass * sim.time_step
    return (T - D - Fg) / mass


def nose_heat_flux(temperature, velocity, height, effective_radius, emmisivity=.8):
    # sutton-graves
    heat_flux_in = k * (velocity ** 3) * math.sqrt(atmospheric_density(height) / effective_radius)
    heat_flux_out = emmisivity * sigma * ((temperature ** 4) - (293 ** 4))
    return max(0, heat_flux_in - heat_flux_out)


def max_temperature(velocity, height, effective_radius, emmisivity=.8):
    return (k / (emmisivity * sigma) * (velocity ** 3) * math.sqrt(
        atmospheric_density(height) / effective_radius) + 293**4) ** (1 / 4)


def angular_velocity(thrust, velocity, mass, height, a, gamma):
    T = thrust * math.sin(a)  # perpendicular to the flight direction
    c = (-gravitational_acceleration(height) + (velocity ** 2) / (earth_radius + height))
    return (math.cos(gamma) * c + T / mass) / velocity


class GravityTurn:
    def __init__(self, start, end, angle):
        self.start = start
        self.end = end
        self.angle = angle


class FlightSim:
    loss_gravity = 0
    loss_drag = 0
    deltaV = 0

    def __init__(self, stages, gravity_turn: GravityTurn, target_orbit=0, time_step=0.2):
        self.stages = stages
        self.time_step = time_step
        self.gravity_turn = gravity_turn
        self.target_orbit = target_orbit

    def simulate(self):
        t = 0  # passed time
        v = 0  # velocity
        m = 0  # mass
        temp = 0  # temperature
        local_horizon = 0  # angle of the local horizon in radians
        h = 0  # height
        a = 0  # angle of the rocket in radians
        gamma = math.pi * 0.5  # angle of the velocity in respect to the local horizon in radians

        state = []

        # ascent
        for i, stage in enumerate(self.stages):
            stage_time = 0
            print(f'Igniting stage {i + 1} after {t}s - {stage.burn_time}s burn time')
            # calculate the mass of the rest of the rocket
            eff_payload_mass = sum(s.mass_at_time(0) for s in self.stages[i + 1:])
            orbit = None

            # iterate
            while stage_time < stage.burn_time:
                m = eff_payload_mass + stage.mass_at_time(stage_time)
                v += acceleration_in_dir_of_flight(stage.thrust, v, m, h, a, gamma, self) * self.time_step
                h += v * math.cos(math.pi/2-gamma) * self.time_step
                gamma += angular_velocity(stage.thrust, v, m, h, a, gamma) * self.time_step
                temp = max_temperature(v, h, effective_nose_radius)
                stage_time += self.time_step
                t += self.time_step

                a = math.radians(self.gravity_turn.angle) if self.gravity_turn.start < h < self.gravity_turn.end else 0

                local_horizon += math.atan(v * self.time_step * math.cos(gamma) / (earth_radius + h))

                state.append((t, h, v, m, a, gamma, local_horizon, temp, 'Ascent'))

                if i == len(self.stages) - 1:
                    orbit = Orbit(h, v, gamma)
                    if orbit.apoapsis_height >= self.target_orbit > 0:
                        print(f'Apoapsis at target height - shutting off at [{t}s]')
                        break

            if i == len(self.stages) - 1 and self.target_orbit > 0:
                # wait for the rocket to reach the apoapsis
                while h > 0 and abs(orbit.apoapsis_height - h) > self.target_orbit*0.001:
                    h += v * math.cos(math.pi/2-gamma) * self.time_step
                    gamma += angular_velocity(stage.thrust, v, m, h, a, gamma) * self.time_step
                    temp = max_temperature(v, h, effective_nose_radius)
                    t += self.time_step
                    local_horizon += math.atan(v * self.time_step * math.cos(gamma) / (earth_radius + h))
                    state.append((t, h, v, m, a, gamma, local_horizon, temp, 'Waiting for apoapsis'))
                    orbit = Orbit(h, v, gamma)
                print(f'Apoapsis reached: {round(h/1000,1)} km - circularizing [{t}s]')

                # circularize
                min_periapsis = h - 10000
                while h > 0 and orbit.periapsis_height < self.target_orbit * .95 and stage_time < stage.burn_time:
                    # wait for the rocket to reach the apoapsis
                    m = eff_payload_mass + stage.mass_at_time(stage_time)
                    v += acceleration_in_dir_of_flight(stage.thrust, v, m, h, a, gamma, self) * self.time_step
                    h += v * math.cos(math.pi/2-gamma) * self.time_step
                    gamma += angular_velocity(stage.thrust, v, m, h, a, gamma) * self.time_step
                    temp = max_temperature(v, h, effective_nose_radius)
                    stage_time += self.time_step
                    t += self.time_step
                    local_horizon += math.atan(v * self.time_step * math.cos(gamma) / (earth_radius + h))
                    state.append((t, h, v, m, a, gamma, local_horizon, temp, 'Circularizing'))
                    orbit = Orbit(h, v, gamma)

        print(f'Loss due to gravity: {self.loss_gravity} m/s')
        print(f'Loss due to drag: {self.loss_drag} m/s')
        print(f'Total deltaV: {self.deltaV} m/s')
        return state
