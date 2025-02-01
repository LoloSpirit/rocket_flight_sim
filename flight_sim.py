import copy
import math

from physics import Physics, earth_radius
from dataclasses import dataclass

from orbit import Orbit

# constants for this simulation
effective_area = 15  # m^2
effective_nose_radius = 0.5  # m

class GravityTurn:
    """Defines the start, end, and angle of a gravity turn."""
    def __init__(self, start, end, angle):
        self.start = start
        self.end = end
        self.angle = angle


@dataclass
class State:
    """Stores the current state of the rocket."""
    t = 0  # passed time
    v = 0  # velocity
    m = 0  # mass
    temp = 0  # temperature
    local_horizon = 0  # angle of the local horizon in radians
    h = 0  # height
    a = 0  # angle of the rocket in radians
    gamma = math.pi * 0.5  # angle of the velocity in respect to the local horizon in radians
    orbit = None
    description = ''


class FlightSim:
    """Simulates a rocket launch and ascent."""
    loss_gravity = 0
    loss_drag = 0
    deltaV = 0

    def __init__(self, stages, gravity_turn: GravityTurn, target_orbit=0, circularize=False, time_step=0.02):
        self.stages = stages
        self.time_step = time_step
        self.gravity_turn = gravity_turn
        self.circ = circularize
        self.target_orbit = target_orbit

    def simulate(self):
        """Runs the simulation and returns the flight states."""
        simulation_states = []

        state = State()
        state.orbit = Orbit(state.h, state.v, state.gamma)

        # ascent phase
        for i, stage in enumerate(self.stages):
            stage_time = 0
            print(f'Igniting stage {i + 1} after {state.t}s - {stage.burn_time}s burn time')

            # calculate the mass of the rest of the rocket
            eff_payload_mass = sum(s.mass_at_time(0) for s in self.stages[i + 1:])
            last_stage = i == len(self.stages) - 1

            # iterate through burn time
            while stage_time < stage.burn_time:
                self.advance_state(state, stage, stage_time, eff_payload_mass)
                state.description = 'Ascent'

                # copy the state so it is not just a reference
                simulation_states.append(copy.deepcopy(state))
                stage_time += self.time_step

                # if a target orbit is specified - circularize on the last stage
                if last_stage:
                    if state.orbit.apoapsis_height >= self.target_orbit:
                        if self.circ:
                            print(f'Apoapsis at target height - shutting off at [{state.t}s]')
                            self.circularize(state, stage, stage_time, eff_payload_mass, simulation_states)
                            break
                        elif simulation_states[-2].orbit.eccentricity < state.orbit.eccentricity:
                            # break when orbit eccentricity starts to increase again
                            print(f'Periapsis at target height - shutting off at [{state.t}s]')
                            break

        print(f'Loss due to gravity: {self.loss_gravity} m/s')
        print(f'Loss due to drag: {self.loss_drag} m/s')
        print(f'Total deltaV: {self.deltaV} m/s')
        print(f'Fuel left: {state.m - (self.stages[-1].payload_mass + self.stages[-1].structure_mass) * 1000} kg')

        return simulation_states

    def advance_state(self, state, stage, stage_time, eff_payload_mass, engines_on=True):
        """Advances the state by one time step."""
        if engines_on:
            state.m = eff_payload_mass + stage.mass_at_time(stage_time)
            stage_time += self.time_step

        thrust = stage.thrust if engines_on else 0
        state.v += Physics.acceleration_in_dir_of_flight(thrust, state, effective_area, self) * self.time_step
        state.h += state.v * math.cos(math.pi / 2 - state.gamma) * self.time_step
        state.gamma += Physics.angular_velocity(stage.thrust, state) * self.time_step
        state.temp = Physics.max_temperature(state.v, state.h, effective_nose_radius)
        state.t += self.time_step
        state.orbit.update(state.h, state.v, state.gamma)

        # apply gravity turn adjustments
        if self.gravity_turn.start < state.h < self.gravity_turn.end:
            state.a = math.radians(self.gravity_turn.angle)
        else:
            state.a = 0

        # update local horizon angle
        state.local_horizon += math.atan(state.v * self.time_step * math.cos(state.gamma) / (earth_radius + state.h))

    def circularize(self, state, stage, stage_time, eff_payload_mass, simulation_states):
        """Performs orbit circularization at apoapsis."""
        if self.target_orbit <= 0:
            return

        # coast to apoapsis
        while state.h > simulation_states[-2].h:
            self.advance_state(state, stage, 0, 0, False)
            state.description = 'Waiting for apoapsis'
            simulation_states.append(copy.deepcopy(state))

        print(f'Apoapsis reached: {round(state.h / 1000, 1)} km - circularizing [{state.t}s]')

        # perform circularization burn
        while stage_time < stage.burn_time:
            self.advance_state(state, stage, stage_time, eff_payload_mass)
            stage_time += self.time_step
            state.description = 'Circularizing'
            simulation_states.append(copy.deepcopy(state))

            if simulation_states[-2].orbit.eccentricity < state.orbit.eccentricity:
                break