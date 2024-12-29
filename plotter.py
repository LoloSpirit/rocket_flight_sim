import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider

import flight_sim


class Plotter:
    def __init__(self, result):
        self.time = [r[0] for r in result]
        self.height = [r[1] for r in result]
        self.velocity = [r[2] for r in result]
        self.mass = [r[3] for r in result]
        self.angle = [r[4] for r in result]
        self.gamma = [r[5] for r in result]
        self.local_horizon = [r[6] for r in result]

    def plot(self):
        # Create a figure with GridSpec
        fig = plt.figure(figsize=(10, 6))
        gs = GridSpec(3, 2, width_ratios=[1, 1])  # Left side is wider
        ax1 = fig.add_subplot(gs[0, 1])
        ax2 = fig.add_subplot(gs[1, 1], sharex=ax1)
        ax3 = fig.add_subplot(gs[2, 1], sharex=ax1)
        ax_left = fig.add_subplot(gs[:, 0])

        plt.subplots_adjust(bottom=0.25)  # Adjust to make room for the slider

        # Set up the slider
        ax_freq = plt.axes([0.2, 0.1, 0.65, 0.03], facecolor="black")
        plt.subplots_adjust(hspace=0.5)
        plt.title = "Rocket ascent trajectory"
        time_slider = Slider(
            ax=ax_freq,
            label="Time",
            valmin=0.1,
            valmax=self.time[-1],
            valinit=self.time[-1],
            valstep=.1,
        )

        def update_trajectory(val):
            time = time_slider.val
            # closest time index
            idx = min(range(len(self.time)), key=lambda i: abs(self.time[i] - time))

            # calculate the trajectory parameters to construct an ellipse
            distance = flight_sim.earth_radius + self.height[idx]
            mu = flight_sim.gravitational_constant * flight_sim.earth_mass
            energy = 0.5 * (self.velocity[idx]) ** 2 - mu / distance
            semi_major_axis = -mu / (2 * energy)
            angular_momentum = distance * self.velocity[idx] * math.cos(self.gamma[idx])
            eccentricity = (1 + 2 * energy * angular_momentum ** 2 / (mu ** 2)) ** 0.5

            # find the intersections with a circle with the radius with earth and height of the rocket
            intersections_earth = self.ellipse_circle_intersections(semi_major_axis, eccentricity, flight_sim.earth_radius)
            intersections_rocket = self.ellipse_circle_intersections(semi_major_axis, eccentricity, distance)
            if len(intersections_earth) == 0:
                intersections_earth = [0, 2 * np.pi]

            # calculate the angle by which the ellipse has to be rotated to align with the rockets position
            offset_angle = self.local_horizon[idx] - (intersections_rocket[1] - np.pi)

            # trace the ellipse between the first and second earth intersections
            x = []
            y = []
            try:
                angle = intersections_earth[0]
                delta = intersections_earth[1] - intersections_earth[0]
                for i in range(5000):
                    r = semi_major_axis * (1 - eccentricity ** 2) / (1 + eccentricity * math.cos(angle))
                    # adding the offset angle rotates the ellipse
                    x.append(r * math.sin(angle - offset_angle))
                    y.append(-r * math.cos(angle - offset_angle))

                    angle += delta / 5000

            except ZeroDivisionError:
                pass

            rocket_pos = distance * math.sin(self.local_horizon[idx]), distance * math.cos(self.local_horizon[idx])

            # Update the plots
            ax_left.clear()
            velocity_angle = self.local_horizon[idx] + (np.pi/2 - self.gamma[idx])
            rocket = plt.Arrow(rocket_pos[0], rocket_pos[1], self.height[idx] * math.sin(velocity_angle), self.height[idx] * math.cos(velocity_angle), width=self.height[idx] / 20, color='green')
            ax_left.plot(rocket_pos[0], rocket_pos[1], color='green', marker='o', markersize=5)
            ax_left.plot(x,y, color='red')
            ax_left.add_artist(earth)
            ax_left.add_artist(rocket)

            ax_left.set_aspect('equal')

            # plot additional points to define min size for t=0
            ax_left.plot(-10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
            ax_left.plot(10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
            ax_left.plot(rocket_pos[0], max(10, 2 * self.height[idx]) + flight_sim.earth_radius, color='black', marker='o', markersize=.1)

            # plot points to show current value in the graphs
            height_pos.set_data(self.time[idx], 0.001 * self.height[idx])
            mass_pos.set_data(self.time[idx], 0.001 * self.mass[idx])
            vel_pos.set_data(self.time[idx], self.velocity[idx])

            fig.canvas.draw_idle()  # Redraw the figure

        # draw the earth
        earth = plt.Circle((0, 0), flight_sim.earth_radius, color='black')
        ax_left.add_artist(earth)
        ax_left.set_title('Trajectory')
        ax_left.set_xlabel('x [m]')
        ax_left.set_ylabel('y [m]')

        # attach the update function to the slider
        time_slider.on_changed(update_trajectory)

        ax1.plot(self.time, [h * 0.001 for h in self.height])
        height_pos, = ax1.plot((0,0), 'ro', color='black')
        ax1.set_title('Height over time')
        ax1.set_ylabel('Height [km]')

        ax2.plot(self.time, self.velocity)
        vel_pos, = ax2.plot((0,0), 'ro', color='black')
        ax2.set_title('Velocity over time')
        ax2.set_ylabel('Velocity [m/s]')

        ax3.plot(self.time, [m * 0.001 for m in self.mass])
        mass_pos, = ax3.plot((0,0), 'ro', color='black')
        ax3.set_title('Mass over time')
        ax3.set_ylabel('Mass [t]')
        ax3.set_xlabel('Time [s]')

        update_trajectory(self.time[0])
        plt.show()

    @staticmethod
    def ellipse_circle_intersections(a, e, R):
        # calculate the argument for the arccos function
        argument = (a * (1 - e ** 2) - R) / (R * e)

        if argument < -1 or argument > 1:
            return []

        # calculate the two intersection angles
        theta1 = math.acos(argument)
        theta2 = 2 * np.pi - theta1  # symmetry

        intersection_points = [theta1, theta2]

        return intersection_points
