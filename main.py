import flight_sim
from flight_sim import FlightSim
from stage import Stage, optimize_staging_two_stages
from plotter import Plotter

stages = [Stage(20, 200, 3500, 1500, 0),
          Stage(5, 50, 3500, 150, 10)]

# task 1 - no optimisation
gravity_turn = flight_sim.GravityTurn(250, 3000, 3.71)
sim = FlightSim(stages, gravity_turn, 270000, time_step=0.01)
result = sim.simulate()

Plotter(result).plot()

# task 2 - optimised staging and circularisation
stages = optimize_staging_two_stages(stages, 1/11, 10, 1000)

gravity_turn = flight_sim.GravityTurn(1000, 9250, 8.4)
sim = FlightSim(stages, gravity_turn, 270000, True, time_step=0.01)
result = sim.simulate()

Plotter(result).plot()


