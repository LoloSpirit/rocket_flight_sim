import flight_sim
from flight_sim import FlightSim
from plotter import Plotter
from rocket_flight_sim.input_reader import read_staging_output

stage1, stage2 = read_staging_output('input.txt')
stages = [stage1, stage2]

# task 1 - no optimisation
gravity_turn = flight_sim.GravityTurn(1000, 3500, 3)
sim = FlightSim(stages, gravity_turn, 400000, True, time_step=0.01)
result = sim.simulate()

plotter = Plotter(result)
plotter.plot()
plotter.export_gif()

# task 2 - optimised staging and circularisation
#stages = optimize_staging_two_stages(stages, 1/11, 10, 1000)

#gravity_turn = flight_sim.GravityTurn(1000, 9250, 8.4)
#sim = FlightSim(stages, gravity_turn, 270000, True, time_step=0.01)
#result = sim.simulate()

#Plotter(result).plot()
