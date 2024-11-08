import math

gravitational_constant = 6.67430 * 10 ** -11  # m^3 kg^-1 s^-2
earth_mass = 5.972 * 10 ** 24  # kg
earth_radius = 6371000  # m
effective_area = 15  # m^2


def gravitational_acceleration(height):
    return gravitational_constant * earth_mass / ((earth_radius + height) ** 2)


def atmospheric_density(height):
    return 1.2 * math.e ** (-1.244268 * (10 ** -4) * height)


def acceleration_in_dir_of_flight(thrust, velocity, mass, height, a, gamma):
    T = thrust * math.cos(a)  # in the direction of the flight
    D = atmospheric_density(height) * (velocity ** 2) * effective_area * 0.5
    Fg = mass * gravitational_acceleration(height)
    return (T - D - Fg * math.sin(gamma)) / mass


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
    def __init__(self, stages, gravity_turn: GravityTurn, time_step=0.1):
        self.stages = stages
        self.time_step = time_step
        self.gravity_turn = gravity_turn

    def simulate(self):
        t = 0  # passed time
        v = 0  # velocity
        m = 0  # mass
        local_horizon = 0  # angle of the local horizon in radians
        h = 0  # height
        a = 0  # angle of the rocket in radians
        gamma = math.pi * 0.5  # angle of the velocity in respect to the local horizon in radians

        state = []

        for i, stage in enumerate(self.stages):
            stage_time = 0
            print(f'Igniting stage {i + 1} after {t}s - {stage.burn_time}s burn time')
            # calculate the mass of the rest of the rocket
            eff_payload_mass = sum(s.mass_at_time(0) for s in self.stages[i + 1:])

            while stage_time < stage.burn_time:
                m = eff_payload_mass + stage.mass_at_time(stage_time)
                v += acceleration_in_dir_of_flight(stage.thrust, v, m, h, a, gamma) * self.time_step
                h += v * math.cos(a) * self.time_step
                gamma += angular_velocity(stage.thrust, v, m, h, a, gamma) * self.time_step
                stage_time += self.time_step
                t += self.time_step

                a = math.radians(self.gravity_turn.angle) if self.gravity_turn.start < h < self.gravity_turn.end else 0

                local_horizon += math.atan(v * self.time_step * math.cos(gamma) / (earth_radius + h))

                state.append((t, h, v, m, a, gamma, local_horizon))

        return state
