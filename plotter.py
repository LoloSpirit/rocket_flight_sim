import math

import matplotlib.pyplot as plt
from orbit import Orbit
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
        self.temperature = [r[7] for r in result]
        self.state = [r[8] for r in result]
        self.orbit = Orbit(self.height[-1], self.velocity[-1], self.gamma[-1])

    def plot(self):
        # Create a figure with GridSpec
        fig = plt.figure(figsize=(10, 8))
        gs = GridSpec(4, 2, width_ratios=[1, 1])  # Left side is wider
        ax1 = fig.add_subplot(gs[0, 1])
        ax2 = fig.add_subplot(gs[1, 1], sharex=ax1)
        ax3 = fig.add_subplot(gs[2, 1], sharex=ax1)
        ax4 = fig.add_subplot(gs[3, 1], sharex=ax1)
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
        text = plt.text(0.5, .6, "s", fontsize=12)

        def update_trajectory(val):
            time = time_slider.val
            # closest time index
            idx = min(range(len(self.time)), key=lambda i: abs(self.time[i] - time))

            # calculate the trajectory parameters to construct an ellipse
            self.orbit.update(self.height[idx], self.velocity[idx], self.gamma[idx])

            # find the intersections with a circle with the radius with earth and height of the rocket
            intersections_earth = self.ellipse_circle_intersections(self.orbit.semi_major_axis, self.orbit.eccentricity, flight_sim.earth_radius)
            intersections_rocket = self.ellipse_circle_intersections(self.orbit.semi_major_axis, self.orbit.eccentricity, self.orbit.distance)
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
                    r = self.orbit.semi_major_axis * (1 - self.orbit.eccentricity ** 2) / (1 + self.orbit.eccentricity * math.cos(angle))
                    # adding the offset angle rotates the ellipse
                    x.append(r * math.sin(angle - offset_angle))
                    y.append(-r * math.cos(angle - offset_angle))

                    angle += delta / 5000

            except ZeroDivisionError:
                pass

            distance = self.orbit.distance
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
            # plot apoapsis and periapsis heights under the graph

            text.set_text(f"$r_p$ = {round(self.orbit.periapsis_height / 1000,1)} km\n"
                          f"$r_a$ = {round(self.orbit.apoapsis_height / 1000,1)} km\n"
                          f"$m_{{remaining}}$ = {round(self.mass[idx] * 0.001, 1)} t\n"
                          f"state: {self.state[idx]}")

            # plot additional points to define min size for t=0
            ax_left.plot(-10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
            ax_left.plot(10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
            ax_left.plot(rocket_pos[0], max(10, 2 * self.height[idx]) + flight_sim.earth_radius, color='black', marker='o', markersize=.1)

            # plot points to show current value in the graphs
            height_pos.set_data(self.time[idx], 0.001 * self.height[idx])
            mass_pos.set_data(self.time[idx], 0.001 * self.mass[idx])
            vel_pos.set_data(self.time[idx], self.velocity[idx])
            temp_pos.set_data(self.time[idx], self.temperature[idx] - 273.15)

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
        ax1.set_ylabel('Height [km]')

        ax2.plot(self.time, self.velocity)
        vel_pos, = ax2.plot((0,0), 'ro', color='black')
        ax2.set_ylabel('Velocity [m/s]')

        ax3.plot(self.time, [m * 0.001 for m in self.mass])
        mass_pos, = ax3.plot((0,0), 'ro', color='black')
        ax3.set_ylabel('Mass [t]')

        ax4.plot(self.time, [t - 273.15 for t in self.temperature])
        temp_pos, = ax4.plot((0,0), 'ro', color='black')
        ax4.set_ylabel('max. Temperature [°C]')
        ax4.set_xlabel('Time [s]')

        print(max([t - 273.15 for t in self.temperature]))

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
