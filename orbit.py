import math
import physics


class Orbit:
    distance = 0
    mu = 0
    energy = 0
    semi_major_axis = 0
    eccentricity = 0
    angular_momentum = 0
    periapsis = 0
    periapsis_height = 0
    apoapsis = 0
    apoapsis_height = 0

    def __init__(self, height, velocity, gamma):
        self.height = height
        self.velocity = velocity
        self.gamma = gamma
        self.update(height, velocity, gamma)

    def update(self, height, velocity, gamma):
        self.distance = physics.earth_radius + height
        self.mu = physics.gravitational_constant * physics.earth_mass
        self.energy = 0.5 * velocity ** 2 - self.mu / self.distance
        self.semi_major_axis = -self.mu / (2 * self.energy)
        self.angular_momentum = self.distance * velocity * math.cos(gamma)
        self.eccentricity = (1 + 2 * self.energy * self.angular_momentum ** 2 / (self.mu ** 2)) ** 0.5

        self.periapsis = self.semi_major_axis * (1 - self.eccentricity)
        self.periapsis_height = self.periapsis - physics.earth_radius

        self.apoapsis = self.semi_major_axis * (1 + self.eccentricity)
        self.apoapsis_height = self.apoapsis - physics.earth_radius
