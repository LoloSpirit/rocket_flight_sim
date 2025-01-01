import flight_sim
from flight_sim import FlightSim
from stage import Stage, optimize_staging_two_stages
from plotter import Plotter

stages = [Stage(20, 200, 3500, 1500, 0),
          Stage(5, 50, 3500, 150, 10)
          ]

stages = optimize_staging_two_stages(stages, 1/11, 11.1, 1000)

#gravity_turn = flight_sim.GravityTurn(250, 3000, 3.71)
gravity_turn = flight_sim.GravityTurn(1000, 8500, 8.395)
sim = FlightSim(stages, gravity_turn, 270000)
result = sim.simulate()

Plotter(result).plot()