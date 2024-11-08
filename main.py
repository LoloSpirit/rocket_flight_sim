import flight_sim
from flight_sim import FlightSim
from stage import Stage
from plotter import Plotter

stages = [Stage(20, 200, 3500, 1500, 0),
          Stage(5, 50, 3500, 150, 10)
          ]

gravity_turn = flight_sim.GravityTurn(250, 3000, 3.71)
sim = FlightSim(stages, gravity_turn)
result = sim.simulate()

Plotter(result).plot()