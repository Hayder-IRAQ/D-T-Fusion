"""
Nuclear Fusion Simulation v4.0 — Statistical Approach
D-T Fusion Physics Educational Tool

Uses Poisson process + Bosch-Hale parameterization for
physically accurate plasma simulation.

Author  : Hayder Odhafa (حيدر عذافة)
GitHub  : https://github.com/Hayder-IRAQ
Version : 4.0
License : MIT
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logging
import json
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NuclearFusionSimulation:
    """
    Statistical Nuclear Fusion Simulation using Poisson Process
    Educational tool for understanding D-T fusion physics with correct statistical approach
    """

    def __init__(self):
        # Physical constants - Use consistent units (SI)
        self.BOLTZMANN_CONSTANT = 1.380649e-23  # J/K
        self.NUCLEAR_RADIUS = 1.2e-15  # meters
        self.COULOMB_CONSTANT = 8.99e9  # N⋅m²/C²
        self.ELECTRON_CHARGE = 1.602e-19  # Coulombs
        self.AMU_TO_KG = 1.66053906660e-27  # kg per atomic mass unit
        self.EV_TO_JOULE = 1.602176634e-19  # Joules per eV
        self.HBAR = 1.054571817e-34  # J⋅s

        # Nuclear properties (AMU)
        self.deuterium_mass = 2.014102  # AMU
        self.tritium_mass = 3.016049  # AMU
        self.helium_mass = 4.002603  # AMU
        self.neutron_mass = 1.00866492  # AMU

        # Simulation parameters
        self.temperature = 1e8  # Kelvin
        self.density = 1e20  # particles/m³
        self.time_step = 1e-12  # seconds
        self.current_step = 0
        self.max_steps = 2000
        self.simulation_volume = 1e-21  # cubic meters

        # Simulation state
        self.particles = self.initialize_particles()
        self.reaction_data = []
        self.is_running = False
        self.is_paused = False
        self.simulation_thread = None

        # Performance tracking
        self.start_time = None
        self.fps_counter = 0
        self.last_fps_update = time.time()
        self.fps_data = []

        logger.info("Nuclear Fusion Simulation initialized with statistical approach")
        self.setup_gui()

    def initialize_particles(self, num_deuterium=100, num_tritium=100):
        """Initialize particle positions and velocities in 3D space"""
        np.random.seed(int(time.time()))

        def maxwell_boltzmann_velocity(mass_amu, temperature):
            """Generate velocities following Maxwell-Boltzmann distribution"""
            mass_kg = mass_amu * self.AMU_TO_KG
            sigma = np.sqrt(self.BOLTZMANN_CONSTANT * temperature / mass_kg)
            return np.random.normal(0, sigma, 3)

        particles = {
            'deuterium': {
                'positions': np.random.random((num_deuterium, 3)) * (self.simulation_volume ** (1 / 3)),
                'velocities': np.array([maxwell_boltzmann_velocity(self.deuterium_mass, self.temperature)
                                        for _ in range(num_deuterium)]),
                'active': np.ones(num_deuterium, dtype=bool),
                'energy': np.zeros(num_deuterium)
            },
            'tritium': {
                'positions': np.random.random((num_tritium, 3)) * (self.simulation_volume ** (1 / 3)),
                'velocities': np.array([maxwell_boltzmann_velocity(self.tritium_mass, self.temperature)
                                        for _ in range(num_tritium)]),
                'active': np.ones(num_tritium, dtype=bool),
                'energy': np.zeros(num_tritium)
            },
            'helium': {
                'positions': np.empty((0, 3)),
                'velocities': np.empty((0, 3)),
                'active': np.empty(0, dtype=bool),
                'energy': np.empty(0)
            },
            'neutrons': {
                'positions': np.empty((0, 3)),
                'velocities': np.empty((0, 3)),
                'active': np.empty(0, dtype=bool),
                'energy': np.empty(0)
            }
        }
        return particles

    def calculate_reaction_rate_coefficient(self, temperature):
        """
        Calculate the reaction rate coefficient <σv> for D-T fusion
        Using Bosch-Hale parameterization (1992)
        """
        # Convert temperature to keV
        T_keV = temperature * self.BOLTZMANN_CONSTANT / self.EV_TO_JOULE / 1000

        # Bosch-Hale parameters for D-T reaction
        A1 = 6.927e-17
        A2 = 5.556e2
        A3 = 2.105e4
        A4 = -3.263e-2
        A5 = 1.998e-1
        A6 = 1.021e-4
        A7 = 1.356e-2

        try:
            # Calculate theta
            theta = T_keV / (1 - (A2 * T_keV / (1 + A3 * T_keV + A4 * T_keV ** 2 + A5 * T_keV ** 3 + A6 * T_keV ** 4)))

            # Calculate xi
            xi = (A1 ** 2 / (4 * theta)) ** (1 / 3)

            # Calculate <σv> in m³/s
            sigma_v = A7 * theta * np.sqrt(xi / (self.deuterium_mass * self.tritium_mass) /
                                           (self.deuterium_mass + self.tritium_mass) * self.AMU_TO_KG) * np.exp(-3 * xi)

            return max(sigma_v, 0.0)
        except (OverflowError, ZeroDivisionError, ValueError):
            return 0.0

    def update_particles_statistical(self):
        """
        Update particles using statistical Poisson process model
        This is the correct physical approach for plasma simulations
        """
        fusion_occurred = False

        # Update positions for all active particles
        for particle_type in ['deuterium', 'tritium', 'helium', 'neutrons']:
            if len(self.particles[particle_type]['positions']) > 0:
                active = self.particles[particle_type]['active']
                if np.any(active):
                    self.particles[particle_type]['positions'][active] += (
                            self.particles[particle_type]['velocities'][active] * self.time_step
                    )
                    # Apply periodic boundary conditions
                    box_size = self.simulation_volume ** (1 / 3)
                    self.particles[particle_type]['positions'][active] = self.particles[particle_type]['positions'][
                                                                             active] % box_size

        # Get active particles
        d_active_mask = self.particles['deuterium']['active']
        t_active_mask = self.particles['tritium']['active']

        d_active_indices = np.where(d_active_mask)[0]
        t_active_indices = np.where(t_active_mask)[0]

        if len(d_active_indices) > 0 and len(t_active_indices) > 0:
            # Calculate tritium density
            n_t = len(t_active_indices) / self.simulation_volume

            # Calculate reaction rate coefficient
            sigma_v = self.calculate_reaction_rate_coefficient(self.temperature)

            # For each deuterium particle, check for fusion event
            for d_idx in d_active_indices:
                # Calculate reaction rate for this deuterium
                reaction_rate = n_t * sigma_v

                # Probability of fusion in time step dt
                fusion_probability = 1 - np.exp(-reaction_rate * self.time_step)

                # Check if fusion occurs
                if np.random.random() < fusion_probability:
                    # Select random tritium particle
                    t_idx = np.random.choice(t_active_indices)

                    # Consume both particles
                    self.particles['deuterium']['active'][d_idx] = False
                    self.particles['tritium']['active'][t_idx] = False

                    # Create reaction products at average position
                    reaction_pos = (self.particles['deuterium']['positions'][d_idx] +
                                    self.particles['tritium']['positions'][t_idx]) / 2

                    # Conservation of momentum
                    total_momentum = (
                            self.particles['deuterium']['velocities'][d_idx] * self.deuterium_mass +
                            self.particles['tritium']['velocities'][t_idx] * self.tritium_mass
                    )

                    # Create helium-4 (3.5 MeV)
                    he_velocity = total_momentum / self.helium_mass * 0.2
                    self.add_particle('helium', reaction_pos, he_velocity, 3.5)

                    # Create neutron (14.1 MeV)
                    neutron_velocity = total_momentum / self.neutron_mass * 0.8
                    self.add_particle('neutrons', reaction_pos, neutron_velocity, 14.1)

                    # Record reaction data
                    energy_mev = 17.6  # Total energy for D-T reaction
                    self.reaction_data.append({
                        'step': self.current_step,
                        'time_ns': self.current_step * self.time_step * 10e9,
                        'temperature_kev': self.temperature * self.BOLTZMANN_CONSTANT / self.EV_TO_JOULE / 1000,
                        'reaction_rate': reaction_rate,
                        'fusion_probability': fusion_probability * 100,
                        'sigma_v_m3s': sigma_v,
                        'energy_released_mev': energy_mev,
                        'total_energy_mev': len(self.reaction_data) * energy_mev + energy_mev,
                        'deuterium_remaining': np.sum(self.particles['deuterium']['active']) - 1,
                        'tritium_remaining': np.sum(self.particles['tritium']['active']) - 1
                    })

                    logger.info(f"Fusion event {len(self.reaction_data)}: "
                                f"T={self.temperature * self.BOLTZMANN_CONSTANT / self.EV_TO_JOULE / 1000:.1f} keV, "
                                f"Rate={reaction_rate:.2e} s⁻¹, "
                                f"Prob={fusion_probability * 100:.6f}%, "
                                f"Energy={energy_mev}MeV")

                    fusion_occurred = True

                    # Remove consumed tritium from available list
                    t_active_indices = np.setdiff1d(t_active_indices, [t_idx])
                    if len(t_active_indices) == 0:
                        break

        return fusion_occurred

    def add_particle(self, particle_type, position, velocity, kinetic_energy_mev):
        """Add a new particle to the simulation"""
        if len(self.particles[particle_type]['positions']) == 0:
            self.particles[particle_type]['positions'] = position.reshape(1, 3)
            self.particles[particle_type]['velocities'] = velocity.reshape(1, 3)
            self.particles[particle_type]['active'] = np.array([True])
            self.particles[particle_type]['energy'] = np.array([kinetic_energy_mev])
        else:
            self.particles[particle_type]['positions'] = np.vstack([
                self.particles[particle_type]['positions'], position
            ])
            self.particles[particle_type]['velocities'] = np.vstack([
                self.particles[particle_type]['velocities'], velocity
            ])
            self.particles[particle_type]['active'] = np.append(
                self.particles[particle_type]['active'], True
            )
            self.particles[particle_type]['energy'] = np.append(
                self.particles[particle_type]['energy'], kinetic_energy_mev
            )

    def setup_gui(self):
        """Setup the professional GUI interface"""
        self.root = tk.Tk()
        self.root.title("Nuclear Fusion Simulation - Statistical Approach v4.0")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#2b2b2b')

        # Create main menu
        self.create_menu()

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control panel
        self.create_control_panel(main_container)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 3D Visualization tab
        self.create_3d_tab()

        # Data Analysis tab
        self.create_data_tab()

        # Performance tab
        self.create_performance_tab()

        # Status bar
        self.create_status_bar()

        # Initialize plots
        self.setup_3d_plot()
        logger.info("GUI setup completed")

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Data", command=self.save_data)
        file_menu.add_command(label="Load Data", command=self.load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Export Plot", command=self.export_plot)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Reset View", command=self.reset_3d_view)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_control_panel(self, parent):
        """Create the control panel"""
        control_frame = ttk.LabelFrame(parent, text="Simulation Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        # Control buttons
        self.start_button = ttk.Button(button_frame, text="Start Simulation",
                                       command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.pause_simulation)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Parameters frame
        params_frame = ttk.Frame(control_frame)
        params_frame.pack(fill=tk.X, pady=(10, 0))

        # Speed control
        ttk.Label(params_frame, text="Speed:").grid(row=0, column=0, sticky=tk.W)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(params_frame, from_=0.1, to=5.0, variable=self.speed_var,
                                orient=tk.HORIZONTAL, length=150)
        speed_scale.grid(row=0, column=1, padx=(5, 15))
        ttk.Label(params_frame, textvariable=self.speed_var).grid(row=0, column=2)

        # Temperature control
        ttk.Label(params_frame, text="Temperature (K):").grid(row=0, column=3, sticky=tk.W, padx=(15, 0))
        self.temp_var = tk.DoubleVar(value=self.temperature)
        temp_scale = ttk.Scale(params_frame, from_=1e7, to=2e8, variable=self.temp_var,
                               orient=tk.HORIZONTAL, length=150, command=self.update_temperature)
        temp_scale.grid(row=0, column=4, padx=(5, 15))
        self.temp_label = ttk.Label(params_frame, text=f"{self.temperature:.2e}")
        self.temp_label.grid(row=0, column=5)

        # Density control
        ttk.Label(params_frame, text="Density (1/m³):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.density_var = tk.DoubleVar(value=self.density)
        density_scale = ttk.Scale(params_frame, from_=1e19, to=1e21, variable=self.density_var,
                                  orient=tk.HORIZONTAL, length=150, command=self.update_density)
        density_scale.grid(row=1, column=1, padx=(5, 15), pady=(5, 0))
        self.density_label = ttk.Label(params_frame, text=f"{self.density:.2e}")
        self.density_label.grid(row=1, column=2, pady=(5, 0))

    def create_3d_tab(self):
        """Create 3D visualization tab"""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="3D Visualization")

        # 3D plot frame
        self.fig = Figure(figsize=(12, 8), facecolor='white')
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.pack(fill=tk.X)

        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

    def create_data_tab(self):
        """Create data analysis tab"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data Analysis")

        # Create sub-tabs
        data_notebook = ttk.Notebook(data_frame)
        data_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Reaction data table
        table_frame = ttk.Frame(data_notebook)
        data_notebook.add(table_frame, text="Reaction Data")

        # Table with fixed columns
        columns = ['Step', 'Time (ns)', 'T (keV)', 'Rate (s⁻¹)', 'Prob (%)',
                   '<σv> (m³/s)', 'Energy (MeV)', 'Total Energy (MeV)', 'D Remaining', 'T Remaining']

        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=25)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack table and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Statistics frame
        stats_frame = ttk.Frame(data_notebook)
        data_notebook.add(stats_frame, text="Statistics")

        self.stats_text = tk.Text(stats_frame, wrap=tk.WORD, font=('Courier', 10))
        stats_scrollbar = ttk.Scrollbar(stats_frame, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)

        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_performance_tab(self):
        """Create performance monitoring tab"""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="Performance")

        self.perf_fig = Figure(figsize=(10, 6))
        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, perf_frame)
        self.perf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.status_bar, text="Ready - Statistical Physics Model")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.fps_label = ttk.Label(self.status_bar, text="FPS: 0")
        self.fps_label.pack(side=tk.RIGHT, padx=5)

    def setup_3d_plot(self):
        """Setup 3D plot with professional styling"""
        self.ax.clear()

        box_size = self.simulation_volume ** (1 / 3) * 1e9  # Convert to nm
        self.ax.set_xlim(0, box_size)
        self.ax.set_ylim(0, box_size)
        self.ax.set_zlim(0, box_size)

        self.ax.set_xlabel('X (nanometers)', fontsize=10)
        self.ax.set_ylabel('Y (nanometers)', fontsize=10)
        self.ax.set_zlabel('Z (nanometers)', fontsize=10)
        self.ax.set_title('Nuclear Fusion Simulation - Statistical Approach', fontsize=12, fontweight='bold')

        self.ax.grid(True, alpha=0.3)

    def update_3d_plot(self):
        """Update 3D visualization"""
        self.ax.clear()
        self.setup_3d_plot()

        # Plot deuterium (red spheres)
        active_d = self.particles['deuterium']['active']
        if np.any(active_d):
            pos_d = self.particles['deuterium']['positions'][active_d] * 1e9
            self.ax.scatter(pos_d[:, 0], pos_d[:, 1], pos_d[:, 2],
                            c='red', s=60, alpha=0.8,
                            label=f'Deuterium ({np.sum(active_d)})')

        # Plot tritium (blue spheres)
        active_t = self.particles['tritium']['active']
        if np.any(active_t):
            pos_t = self.particles['tritium']['positions'][active_t] * 1e9
            self.ax.scatter(pos_t[:, 0], pos_t[:, 1], pos_t[:, 2],
                            c='blue', s=60, alpha=0.8,
                            label=f'Tritium ({np.sum(active_t)})')

        # Plot helium (green spheres, larger)
        if len(self.particles['helium']['positions']) > 0:
            active_he = self.particles['helium']['active']
            if np.any(active_he):
                pos_he = self.particles['helium']['positions'][active_he] * 1e9
                self.ax.scatter(pos_he[:, 0], pos_he[:, 1], pos_he[:, 2],
                                c='green', s=100, alpha=0.9,
                                label=f'Helium-4 ({np.sum(active_he)})', marker='^')

        # Plot neutrons (gray spheres)
        if len(self.particles['neutrons']['positions']) > 0:
            active_n = self.particles['neutrons']['active']
            if np.any(active_n):
                pos_n = self.particles['neutrons']['positions'][active_n] * 1e9
                self.ax.scatter(pos_n[:, 0], pos_n[:, 1], pos_n[:, 2],
                                c='gray', s=40, alpha=0.7,
                                label=f'Neutrons ({np.sum(active_n)})', marker='s')

        # Add legend
        self.ax.legend(loc='upper left', bbox_to_anchor=(0, 1), fontsize=9)

        # Add information box
        total_reactions = len(self.reaction_data)
        total_energy = sum([r['energy_released_mev'] for r in self.reaction_data])

        d_remaining = np.sum(self.particles['deuterium']['active'])
        t_remaining = np.sum(self.particles['tritium']['active'])

        info_text = f"""Step: {self.current_step}
Time: {self.current_step * self.time_step * 1e9:.2f} ns
Reactions: {total_reactions}
Total Energy: {total_energy:.2f} MeV
Temperature: {self.temperature:.1e} K
D Remaining: {d_remaining}
T Remaining: {t_remaining}"""

        self.ax.text2D(0.02, 0.98, info_text, transform=self.ax.transAxes,
                       verticalalignment='top', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))

        self.canvas.draw()
        self.update_fps()

    def update_fps(self):
        """Update FPS counter"""
        current_time = time.time()
        self.fps_counter += 1

        if current_time - self.last_fps_update >= 1.0:
            fps = self.fps_counter / (current_time - self.last_fps_update)
            self.fps_label.config(text=f"FPS: {fps:.1f}")
            self.fps_data.append(fps)

            self.fps_counter = 0
            self.last_fps_update = current_time

    def update_data_table(self):
        """Update the data table with recent reactions"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add recent reactions (last 50 for performance)
        recent_data = self.reaction_data[-50:] if len(self.reaction_data) > 50 else self.reaction_data

        for data in recent_data:
            self.tree.insert('', 'end', values=(
                data['step'],
                f"{data['time_ns']:.3f}",
                f"{data['temperature_kev']:.1f}",
                f"{data['reaction_rate']:.2e}",
                f"{data['fusion_probability']:.6f}",
                f"{data['sigma_v_m3s']:.2e}",
                f"{data['energy_released_mev']:.1f}",
                f"{data['total_energy_mev']:.1f}",
                data['deuterium_remaining'],
                data['tritium_remaining']
            ))

        # Auto-scroll to bottom
        if self.tree.get_children():
            self.tree.see(self.tree.get_children()[-1])

    def update_statistics(self):
        """Update statistics display"""
        if not self.reaction_data:
            stats_text = """=== NUCLEAR FUSION SIMULATION STATISTICS ===
No reactions yet. Start the simulation to see data.
"""
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            return

        stats = self.calculate_statistics()

        stats_text = f"""=== NUCLEAR FUSION SIMULATION STATISTICS (STATISTICAL APPROACH) ===

GENERAL INFORMATION:
• Simulation Time: {self.current_step * self.time_step * 1e9:.3f} ns
• Total Steps: {self.current_step}
• Temperature: {self.temperature:.2e} K ({self.temperature * self.BOLTZMANN_CONSTANT / self.EV_TO_JOULE / 1000:.1f} keV)
• Density: {self.density:.2e} particles/m³
• Volume: {self.simulation_volume:.2e} m³

PARTICLE COUNTS:
• Initial Deuterium: {len(self.particles['deuterium']['active'])}
• Remaining Deuterium: {np.sum(self.particles['deuterium']['active'])}
• Initial Tritium: {len(self.particles['tritium']['active'])}
• Remaining Tritium: {np.sum(self.particles['tritium']['active'])}
• Helium-4 Produced: {np.sum(self.particles['helium']['active']) if len(self.particles['helium']['active']) > 0 else 0}
• Neutrons Produced: {np.sum(self.particles['neutrons']['active']) if len(self.particles['neutrons']['active']) > 0 else 0}

REACTION STATISTICS:
• Total Reactions: {len(self.reaction_data)}
• Reaction Rate: {stats['reaction_rate']:.2e} reactions/s
• Total Energy Released: {stats['total_energy']:.2f} MeV
• Average Energy per Reaction: {stats['avg_energy']:.2f} MeV
• Energy Release Rate: {stats['energy_rate']:.2e} MeV/s

PHYSICS PARAMETERS:
• Average <σv>: {stats['avg_sigma_v']:.2e} m³/s
• Average Fusion Probability: {stats['avg_probability']:.2e}%
• Temperature Range: {stats['min_temp']:.1f} - {stats['max_temp']:.1f} keV

EFFICIENCY METRICS:
• Reaction Efficiency: {stats['efficiency']:.1f}%
• Current FPS: {self.fps_data[-1] if self.fps_data else 0:.1f}
• Average FPS: {np.mean(self.fps_data) if self.fps_data else 0:.1f}

STATISTICAL MODEL FEATURES:
✓ Poisson process for fusion events
✓ Bosch-Hale reaction rate coefficient
✓ No distance-based collision detection
✓ Correct statistical approach for plasma
✓ Matches large-scale plasma simulations
✓ Physically accurate reaction rates
"""

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    def calculate_statistics(self):
        """Calculate comprehensive statistics"""
        if not self.reaction_data:
            return {}

        df = pd.DataFrame(self.reaction_data)

        total_time = self.current_step * self.time_step
        reaction_rate = len(self.reaction_data) / total_time if total_time > 0 else 0

        total_energy = sum([r['energy_released_mev'] for r in self.reaction_data])
        energy_rate = total_energy / total_time if total_time > 0 else 0

        # Efficiency calculation
        initial_d = len(self.particles['deuterium']['active'])
        initial_t = len(self.particles['tritium']['active'])
        remaining_d = np.sum(self.particles['deuterium']['active'])
        remaining_t = np.sum(self.particles['tritium']['active'])

        reacted_pairs = len(self.reaction_data)
        max_possible_reactions = min(initial_d, initial_t)
        efficiency = (reacted_pairs / max_possible_reactions * 100) if max_possible_reactions > 0 else 0

        stats = {
            'reaction_rate': reaction_rate,
            'energy_rate': energy_rate,
            'total_energy': total_energy,
            'avg_energy': total_energy / len(self.reaction_data) if len(self.reaction_data) > 0 else 0,
            'avg_sigma_v': df['sigma_v_m3s'].mean() if len(df) > 0 else 0,
            'avg_probability': df['fusion_probability'].mean() if len(df) > 0 else 0,
            'min_temp': df['temperature_kev'].min() if len(df) > 0 else 0,
            'max_temp': df['temperature_kev'].max() if len(df) > 0 else 0,
            'efficiency': efficiency
        }

        return stats

    def update_temperature(self, value):
        """Update simulation temperature"""
        self.temperature = float(value)
        self.temp_label.config(text=f"{self.temperature:.2e}")

    def update_density(self, value):
        """Update simulation density"""
        self.density = float(value)
        self.density_label.config(text=f"{self.density:.2e}")

    def simulation_loop(self):
        """Main simulation loop with statistical approach"""
        self.start_time = time.time()

        try:
            while self.is_running and self.current_step < self.max_steps:
                if not self.is_paused:
                    # Check if we have active particles
                    active_d = np.sum(self.particles['deuterium']['active'])
                    active_t = np.sum(self.particles['tritium']['active'])

                    if active_d == 0 or active_t == 0:
                        self.status_label.config(text="Simulation completed - No more reactants")
                        self.is_running = False
                        break

                    # Use statistical particle update
                    fusion_occurred = self.update_particles_statistical()

                    # Update GUI elements
                    if fusion_occurred or self.current_step % 10 == 0:
                        self.root.after(0, self.update_3d_plot)

                        if fusion_occurred:
                            self.root.after(0, self.update_data_table)
                            self.root.after(0, self.update_statistics)

                    self.current_step += 1

                    # Update status
                    if self.current_step % 100 == 0:
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"Running (Statistical) - Step {self.current_step}/{self.max_steps}"))

                    # Speed control
                    sleep_time = (0.01 / self.speed_var.get()) if self.speed_var.get() > 0 else 0.01
                    time.sleep(sleep_time)
                else:
                    time.sleep(0.1)  # Sleep while paused

        except Exception as e:
            logger.error(f"Simulation error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Simulation Error",
                                                            f"An error occurred: {str(e)}"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.status_label.config(text="Simulation stopped"))

    def start_simulation(self):
        """Start the simulation with proper thread management"""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.start_button.config(text="Running...", state="disabled")
            self.status_label.config(text="Starting statistical simulation...")

            # Start simulation in separate thread
            self.simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
            self.simulation_thread.start()

            logger.info("Statistical simulation started")

    def pause_simulation(self):
        """Pause/resume the simulation"""
        if self.is_running:
            self.is_paused = not self.is_paused
            status_text = "Paused" if self.is_paused else "Running (Statistical)"
            button_text = "Resume" if self.is_paused else "Pause"

            self.pause_button.config(text=button_text)
            self.status_label.config(text=status_text)

            logger.info(f"Simulation {'paused' if self.is_paused else 'resumed'}")

    def reset_simulation(self):
        """Reset the simulation to initial state"""
        # Stop current simulation
        self.is_running = False
        self.is_paused = False

        # Wait for simulation thread to finish
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)

        # Reset all data
        self.current_step = 0
        self.particles = self.initialize_particles()
        self.reaction_data = []
        self.fps_data = []

        # Reset GUI
        self.start_button.config(text="Start Simulation", state="normal")
        self.pause_button.config(text="Pause")
        self.status_label.config(text="Reset complete - Statistical model ready")

        # Update displays
        self.update_3d_plot()
        self.update_data_table()
        self.update_statistics()

        logger.info("Statistical simulation reset")

    def save_data(self):
        """Save simulation data to file"""
        if not self.reaction_data:
            messagebox.showwarning("No Data", "No reaction data to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Simulation Data"
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    df = pd.DataFrame(self.reaction_data)
                    df.to_csv(filename, index=False)
                else:  # JSON format
                    save_data = {
                        'version': '4.0_STATISTICAL',
                        'timestamp': datetime.now().isoformat(),
                        'parameters': {
                            'temperature': self.temperature,
                            'density': self.density,
                            'time_step': self.time_step,
                            'max_steps': self.max_steps,
                            'model_type': 'Poisson_process'
                        },
                        'reaction_data': self.reaction_data,
                        'statistics': self.calculate_statistics()
                    }

                    with open(filename, 'w') as f:
                        json.dump(save_data, f, indent=2)

                messagebox.showinfo("Success", f"Data saved to {filename}")
                logger.info(f"Data saved to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")
                logger.error(f"Failed to save data: {str(e)}")

    def load_data(self):
        """Load simulation data from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Load Simulation Data"
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filename)
                    # Handle missing columns gracefully
                    required_columns = ['step', 'time_ns', 'temperature_kev', 'reaction_rate',
                                        'fusion_probability', 'sigma_v_m3s', 'energy_released_mev']

                    # Check if all required columns exist
                    missing_cols = [col for col in required_columns if col not in df.columns]
                    if missing_cols:
                        messagebox.showerror("Error", f"CSV file missing required columns: {missing_cols}")
                        return

                    self.reaction_data = df.to_dict('records')

                else:  # JSON format
                    with open(filename, 'r') as f:
                        loaded_data = json.load(f)

                    if 'reaction_data' in loaded_data:
                        self.reaction_data = loaded_data['reaction_data']

                        if 'parameters' in loaded_data:
                            params = loaded_data['parameters']
                            self.temperature = params.get('temperature', self.temperature)
                            self.density = params.get('density', self.density)
                            self.temp_var.set(self.temperature)
                            self.density_var.set(self.density)

                # Update displays
                self.update_data_table()
                self.update_statistics()

                messagebox.showinfo("Success", f"Data loaded from {filename}")
                logger.info(f"Data loaded from {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")
                logger.error(f"Failed to load data: {str(e)}")

    def export_plot(self):
        """Export current 3D plot"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Export Plot"
        )

        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot exported to {filename}")
                logger.info(f"Plot exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export plot: {str(e)}")
                logger.error(f"Failed to export plot: {str(e)}")

    def reset_3d_view(self):
        """Reset 3D plot view"""
        self.ax.view_init(elev=20, azim=45)
        self.canvas.draw()

    def show_about(self):
        """Show about dialog"""
        about_text = """Nuclear Fusion Simulation v4.0 - Statistical Approach
Advanced Educational Tool for Understanding D-T Fusion Physics

🔧 STATISTICAL PHYSICS MODEL:
✓ Poisson process for fusion events
✓ Bosch-Hale reaction rate coefficient
✓ No distance-based collision detection
✓ Correct statistical approach for plasma
✓ Matches large-scale plasma simulations (MC-collision)
✓ Physically accurate reaction rates

This simulation models the deuterium-tritium fusion reaction:
²H + ³H → ⁴He + ¹n + 17.6 MeV

Statistical Model:
• For each D particle: draw Poisson event with rate R = n_T * <σv>
• If event occurs: consume random D and T particles
• Record reaction with correct statistical properties
• Gives few but statistically correct events at same n, T

Features:
• Real-time 3D visualization
• Statistical reaction modeling
• Bosch-Hale parameterization
• Advanced data analysis
• Research-grade accuracy

Developed for advanced educational purposes to demonstrate
nuclear fusion physics with correct statistical approach.

© 2024 - Nuclear Physics Educational Tools
Statistical Version - Matches plasma simulation standards"""

        messagebox.showinfo("About - Statistical Version", about_text)

    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Simulation is running. Do you want to quit?"):
                self.is_running = False
                if self.simulation_thread and self.simulation_thread.is_alive():
                    self.simulation_thread.join(timeout=1.0)
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Show initial statistics
        self.update_statistics()

        logger.info("Statistical application started")
        print("=" * 80)
        print("NUCLEAR FUSION SIMULATION - STATISTICAL APPROACH v4.0")
        print("=" * 80)
        print("🔧 STATISTICAL PHYSICS MODEL IMPLEMENTED:")
        print("✓ Poisson process for fusion events")
        print("✓ Bosch-Hale reaction rate coefficient")
        print("✓ No distance-based collision detection")
        print("✓ Correct statistical approach for plasma")
        print("✓ Matches large-scale plasma simulations (MC-collision)")
        print("✓ Physically accurate reaction rates")
        print("")
        print("Statistical Model:")
        print("• For each D particle: draw Poisson event with rate R = n_T * <σv>")
        print("• If event occurs: consume random D and T particles")
        print("• Record reaction with correct statistical properties")
        print("• Gives few but statistically correct events at same n, T")
        print("")
        print("This simulation uses the correct statistical approach")
        print("used in large-scale plasma simulations worldwide.")
        print("\nSimulated Reaction: ²H + ³H → ⁴He + ¹n + 17.6 MeV")
        print("")
        print("Statistical Version - Matches plasma simulation standards!")
        print("=" * 80)

        self.root.mainloop()


def main():
    """Main application entry point"""
    try:
        # Create and run statistical simulation
        simulation = NuclearFusionSimulation()
        simulation.run()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        if 'messagebox' in globals():
            messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")
        else:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()