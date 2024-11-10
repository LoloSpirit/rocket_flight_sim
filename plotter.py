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

            # calculate the trajectory
            distance = flight_sim.earth_radius + self.height[idx]
            mu = flight_sim.gravitational_constant * flight_sim.earth_mass
            energy = 0.5 * (self.velocity[idx]) ** 2 - mu / distance
            semi_major_axis = -mu / (2 * energy)
            angular_momentum = distance * self.velocity[idx] * math.cos(self.gamma[idx])
            eccentricity = (1 + 2 * energy * angular_momentum ** 2 / (mu ** 2)) ** 0.5

            # trace
            intersections_earth = self.ellipse_circle_intersections(semi_major_axis, eccentricity, flight_sim.earth_radius)
            intersections_rocket = self.ellipse_circle_intersections(semi_major_axis, eccentricity, distance)
            if len(intersections_earth) == 0:
                intersections_earth = [0, 2 * np.pi]

            # align with rocket position
            offset_angle = self.local_horizon[idx] - (intersections_rocket[1] - np.pi)

            x = []
            y = []
            try:
                angle = intersections_earth[0] - offset_angle
                delta = intersections_earth[1] - intersections_earth[0]
                for i in range(5000):
                    true_anomaly = angle + offset_angle
                    r = semi_major_axis * (1 - eccentricity ** 2) / (1 + eccentricity * math.cos(true_anomaly))

                    x.append(r * math.sin(angle))
                    y.append(-r * math.cos(angle))

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

            # plot points to define min size for t=0
            ax_left.plot(-10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
            ax_left.plot(10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
            ax_left.plot(rocket_pos[0], max(10, 2 * self.height[idx]) + flight_sim.earth_radius, color='black', marker='o', markersize=.1)


            ax_left.set_title('Trajectory')
            ax_left.set_xlabel('x [m]')
            ax_left.set_ylabel('y [m]')

            height_pos.center = (self.time[idx], 0.001 * self.height[idx])

            fig.canvas.draw_idle()  # Redraw the figure

        # draw the earth
        earth = plt.Circle((0, 0), flight_sim.earth_radius, color='black')
        ax_left.add_artist(earth)

        height_pos = plt.Circle((0,0), 1, color='black')

        # Attach the update function to the slider
        time_slider.on_changed(update_trajectory)

        ax1.plot(self.time, [h * 0.001 for h in self.height])
        ax1.add_artist(height_pos)
        ax1.set_title('Height over time')
        ax1.set_ylabel('Height [km]')

        ax2.plot(self.time, self.velocity)
        ax2.set_title('Velocity over time')
        ax2.set_ylabel('Velocity [m/s]')

        ax3.plot(self.time, [m * 0.001 for m in self.mass])
        ax3.set_title('Mass over time')
        ax3.set_ylabel('Mass [t]')
        ax3.set_xlabel('Time [s]')

        update_trajectory(self.time[-1])
        plt.show()

    def ellipse_circle_intersections(self, a, e, R):
        # Calculate the argument for the arccos function
        argument = (a * (1 - e ** 2) - R) / (R * e)

        # Check if the argument is within the valid range for arccos
        if argument < -1 or argument > 1:
            return []

        # Calculate the two intersection angles (they will be symmetric)
        theta1 = math.acos(argument)
        theta2 = 2 * np.pi - theta1  # Symmetric angle

        # Intersection points in polar coordinates (r, theta)
        intersection_points = [theta1, theta2]

        return intersection_points
