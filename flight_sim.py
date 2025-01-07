import copy
import math
from physics import Physics, earth_radius
from dataclasses import dataclass

from orbit import Orbit

# constants for this simulation
effective_area = 15  # m^2
effective_nose_radius = 0.5  # m


class GravityTurn:
    def __init__(self, start, end, angle):
        self.start = start
        self.end = end
        self.angle = angle


@dataclass
class State:
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
    loss_gravity = 0
    loss_drag = 0
    deltaV = 0

    def __init__(self, stages, gravity_turn: GravityTurn, target_orbit=0, time_step=0.2):
        self.stages = stages
        self.time_step = time_step
        self.gravity_turn = gravity_turn
        self.target_orbit = target_orbit

    def simulate(self):
        simulation_states = []

        state = State()
        state.orbit = Orbit(state.h, state.v, state.gamma)
        # ascent
        for i, stage in enumerate(self.stages):
            stage_time = 0
            print(f'Igniting stage {i + 1} after {state.t}s - {stage.burn_time}s burn time')
            # calculate the mass of the rest of the rocket
            eff_payload_mass = sum(s.mass_at_time(0) for s in self.stages[i + 1:])
            last_stage = i == len(self.stages) - 1

            # iterate
            while stage_time < stage.burn_time:
                self.advance_state(state, stage, stage_time, eff_payload_mass)
                state.description = 'Ascent'

                # copy the state so it is not just a reference
                simulation_states.append(copy.deepcopy(state))
                stage_time += self.time_step

                # if a target orbit is specified - circularize on the last stage
                if last_stage and self.target_orbit > 0:
                    # check if the apoapsis is reached
                    if state.orbit.apoapsis_height >= self.target_orbit:
                        print(f'Apoapsis at target height - shutting off at [{state.t}s]')
                        self.circularize(state, stage, stage_time, eff_payload_mass, simulation_states)
                        break

        print(f'Loss due to gravity: {self.loss_gravity} m/s')
        print(f'Loss due to drag: {self.loss_drag} m/s')
        print(f'Total deltaV: {self.deltaV} m/s')
        return simulation_states

    def advance_state(self, state, stage, stage_time, eff_payload_mass, engines_on=True):
        # advance the state by a time step and calculate the new values
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

        if self.gravity_turn.start < state.h < self.gravity_turn.end:
            state.a = math.radians(self.gravity_turn.angle)
        else:
            state.a = 0

        state.local_horizon += math.atan(state.v * self.time_step * math.cos(state.gamma) / (earth_radius + state.h))

    def circularize(self, state, stage, stage_time, eff_payload_mass, simulation_states):
        if self.target_orbit <= 0:
            return

        # wait for the rocket to reach the apoapsis if a target orbit is specified
        while state.h > 0 and abs(state.orbit.apoapsis_height - state.h) > self.target_orbit * 0.001:
            self.advance_state(state, stage, 0, 0, False)
            state.description = 'Waiting for apoapsis'
            simulation_states.append(copy.deepcopy(state))

        print(f'Apoapsis reached: {round(state.h / 1000, 1)} km - circularizing [{state.t}s]')

        # circularize
        while state.h > 0 and state.orbit.periapsis_height < self.target_orbit * .95 and stage_time < stage.burn_time:
            # wait for the periapsis to reach the target orbit or until the fuel runs out- because the drag is not
            # considered it may not be reached exactly
            self.advance_state(state, stage, stage_time, eff_payload_mass)
            stage_time += self.time_step
            state.description = 'Circularizing'
            simulation_states.append(copy.deepcopy(state))