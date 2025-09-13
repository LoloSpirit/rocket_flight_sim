import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider
from matplotlib import animation

import flight_sim


class Plotter:
    def __init__(self, result):
        self.time = [state.t for state in result]
        self.height = [state.h for state in result]
        self.velocity = [state.v for state in result]
        self.mass = [state.m for state in result]
        self.angle = [state.a for state in result]
        self.gamma = [state.gamma for state in result]
        self.local_horizon = [state.local_horizon for state in result]
        self.temperature = [state.temp for state in result]
        self.description = [state.description for state in result]
        self.orbit = [state.orbit for state in result]

    def plot(self):
        fig = plt.figure(figsize=(10, 8))
        gs = GridSpec(4, 2, width_ratios=[1, 1])
        ax1 = fig.add_subplot(gs[0, 1])
        ax2 = fig.add_subplot(gs[1, 1], sharex=ax1)
        ax3 = fig.add_subplot(gs[2, 1], sharex=ax1)
        ax4 = fig.add_subplot(gs[3, 1], sharex=ax1)
        ax_left = fig.add_subplot(gs[:, 0])

        plt.subplots_adjust(bottom=0.25)

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

        # Initialize frame and get dynamic elements
        dynamic_elements = self._initialize_frame(fig, ax_left, ax1, ax2, ax3, ax4, text)

        def update_trajectory(val):
            time = val
            # closest time index
            idx = min(range(len(self.time)), key=lambda j: abs(self.time[j] - time))
            self._update_frame(idx, *dynamic_elements)

        # attach the update function to the slider
        time_slider.on_changed(update_trajectory)

        self._update_frame(len(self.time) - 1, *dynamic_elements)
        plt.show()

    def _initialize_frame(self, fig, ax_left, ax1, ax2, ax3, ax4, text):
        # draw the earth
        earth = plt.Circle((0, 0), flight_sim.earth_radius, color='black')
        ax_left.add_artist(earth)
        ax_left.set_title('Trajectory')
        ax_left.set_xlabel('x [m]')
        ax_left.set_ylabel('y [m]')

        # Plot static graphs and create marker points for dynamic updates
        ax1.plot(self.time, [h * 0.001 for h in self.height])
        height_pos, = ax1.plot((0, 0), 'o', color='black')
        ax1.set_ylabel('Height [km]')

        ax2.plot(self.time, self.velocity)
        vel_pos, = ax2.plot((0, 0), 'o', color='black')
        ax2.set_ylabel('Velocity [m/s]')

        ax3.plot(self.time, [m * 0.001 for m in self.mass])
        mass_pos, = ax3.plot((0, 0), 'o', color='black')
        ax3.set_ylabel('Mass [t]')

        ax4.plot(self.time, [t - 273.15 for t in self.temperature])
        temp_pos, = ax4.plot((0, 0), 'o', color='black')
        ax4.set_ylabel('max. Temperature [°C]')
        ax4.set_xlabel('Time [s]')

        # Initialize dynamic plot elements for trajectory
        rocket_line, = ax_left.plot([], [], color='green', marker='o', markersize=5)
        ellipse_line, = ax_left.plot([], [], color='red')
        rocket_arrow = plt.Arrow(0, 0, 0, 0, width=1, color='green')
        ax_left.add_artist(rocket_arrow)

        return (fig, ax_left, earth, rocket_line, ellipse_line, rocket_arrow,
                height_pos, mass_pos, vel_pos, temp_pos, text)

    def _update_frame(self, idx, fig, ax_left, earth, rocket_line, ellipse_line, rocket_arrow,
                      height_pos, mass_pos, vel_pos, temp_pos, text):
        orbit = self.orbit[idx]

        # find the intersections with a circle with the radius with earth and height of the rocket
        intersections_earth = self.ellipse_circle_intersections(orbit, flight_sim.earth_radius)
        intersections_rocket = self.ellipse_circle_intersections(orbit, orbit.distance)
        if len(intersections_earth) == 0:
            intersections_earth = [0, 2 * np.pi]

        ascending = self.height[idx-1] - self.height[idx] < 0
        # calculate the angle by which the ellipse has to be rotated to align with the rockets position
        offset_angle = self.local_horizon[idx] - (intersections_rocket[1 if ascending else 0] - np.pi)

        # trace the ellipse between the first and second earth intersections
        x = []
        y = []
        try:
            angle = intersections_earth[0]
            delta = intersections_earth[1] - intersections_earth[0]
            for i in range(5000):
                r = orbit.semi_major_axis * (1 - orbit.eccentricity**2) / (1 + orbit.eccentricity * math.cos(angle))
                # adding the offset angle rotates the ellipse
                x.append(r * math.sin(angle - offset_angle))
                y.append(-r * math.cos(angle - offset_angle))

                angle += delta / 5000

        except ZeroDivisionError:
            pass

        distance = orbit.distance
        rocket_pos = distance * math.sin(self.local_horizon[idx]), distance * math.cos(self.local_horizon[idx])

        # Update the plots
        ax_left.clear()
        # redraw static earth circle and set labels and aspect
        ax_left.add_artist(earth)
        ax_left.set_title('Trajectory')
        ax_left.set_xlabel('x [m]')
        ax_left.set_ylabel('y [m]')
        ax_left.set_aspect('equal')

        velocity_angle = self.local_horizon[idx] + (np.pi/2 - self.gamma[idx])
        # Create new rocket arrow with updated position and orientation
        new_rocket_arrow = plt.Arrow(rocket_pos[0], rocket_pos[1], self.height[idx] * math.sin(velocity_angle),
                                    self.height[idx] * math.cos(velocity_angle), width=self.height[idx] / 20, color='green')
        ax_left.add_artist(new_rocket_arrow)

        # Update ellipse line
        ellipse_line, = ax_left.plot(x, y, color='red')
        # Update rocket position point
        rocket_line, = ax_left.plot(rocket_pos[0], rocket_pos[1], color='green', marker='o', markersize=5)

        # plot apoapsis and periapsis heights under the graph
        text.set_text(f"$r_p$ = {round(orbit.periapsis_height / 1000,1)} km\n"
                      f"$r_a$ = {round(orbit.apoapsis_height / 1000,1)} km\n"
                      f"$m_{{remaining}}$ = {round(self.mass[idx] * 0.001, 3)} t\n"
                      f"state: {self.description[idx]}")

        # plot additional points to define min size for t=0
        ax_left.plot(-10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
        ax_left.plot(10, flight_sim.earth_radius, color='black', marker='o', markersize=.1)
        ax_left.plot(rocket_pos[0], max(10, 2 * self.height[idx]) + flight_sim.earth_radius, color='black',
                     marker='o', markersize=.1)

        # plot points to show current value in the graphs
        height_pos.set_data([self.time[idx]], [0.001 * self.height[idx]])
        mass_pos.set_data([self.time[idx]], [0.001 * self.mass[idx]])
        vel_pos.set_data([self.time[idx]], [self.velocity[idx]])
        temp_pos.set_data([self.time[idx]], [self.temperature[idx] - 273.15])

        fig.canvas.draw_idle()  # Redraw the figure

    def export_gif(self, filename="trajectory.gif"):
        fig = plt.figure(figsize=(10, 8))
        gs = GridSpec(4, 2, width_ratios=[1, 1])
        ax1 = fig.add_subplot(gs[0, 1])
        ax2 = fig.add_subplot(gs[1, 1], sharex=ax1)
        ax3 = fig.add_subplot(gs[2, 1], sharex=ax1)
        ax4 = fig.add_subplot(gs[3, 1], sharex=ax1)
        ax_left = fig.add_subplot(gs[:, 0])

        plt.subplots_adjust(bottom=0.25, hspace=0.5)

        text = plt.text(0.5, .6, "s", fontsize=12)

        # Initialize frame and get dynamic elements
        dynamic_elements = self._initialize_frame(fig, ax_left, ax1, ax2, ax3, ax4, text)

        def animate(frame_idx):
            self._update_frame(frame_idx, *dynamic_elements)
            return []

        step = 2000
        frames = list(range(0, len(self.time), step)) + [len(self.time) - 1] * 10
        anim = animation.FuncAnimation(fig, animate, frames=frames, interval=100, blit=True)
        anim.save(filename, writer='pillow')
        plt.close(fig)

    @staticmethod
    def ellipse_circle_intersections(orbit, R):
        # calculate the argument for the arccos function
        argument = (orbit.semi_major_axis * (1 - orbit.eccentricity ** 2) - R) / (R * orbit.eccentricity)

        if argument < -1 or argument > 1:
            return []

        # calculate the two intersection angles
        theta1 = math.acos(argument)
        theta2 = 2 * np.pi - theta1  # symmetry

        intersection_points = [theta1, theta2]

        return intersection_points
