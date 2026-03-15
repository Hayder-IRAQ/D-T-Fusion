<div align="center">

# ⚛️ Nuclear Fusion Simulation v4.0
### محاكاة الاندماج النووي — النهج الإحصائي

**Physically accurate D-T fusion plasma simulation using Poisson process and Bosch-Hale parameterization.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243?logo=numpy)](https://numpy.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7%2B-11557c)](https://matplotlib.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Physics](https://img.shields.io/badge/Physics-Plasma%20%7C%20Nuclear-red)]()

</div>

---

## 🔬 The Physics

This simulation models the **Deuterium-Tritium (D-T) fusion reaction**:

```
²H  +  ³H  →  ⁴He (3.5 MeV)  +  ¹n (14.1 MeV)  +  17.6 MeV total
```

Unlike naive collision-detection simulations, this uses the **correct statistical approach** applied in large-scale plasma simulations worldwide:

| Feature | This Simulation | Naive Approach |
|---|---|---|
| Reaction model | ✅ Poisson process | ❌ Distance threshold |
| Rate coefficient | ✅ Bosch-Hale (1992) | ❌ Approximation |
| Particle velocities | ✅ Maxwell-Boltzmann | ❌ Fixed |
| Momentum conservation | ✅ Yes | ❌ No |
| Statistical accuracy | ✅ Research-grade | ❌ Toy model |

---

## ✨ Features

| Category | Details |
|---|---|
| 🧮 **Statistical Model** | Poisson process: for each D particle, fusion probability = `1 - exp(-n_T · <σv> · dt)` |
| 📐 **Bosch-Hale** | Industry-standard parameterization for D-T reaction rate coefficient `<σv>` |
| 🌡️ **Maxwell-Boltzmann** | Particle velocities sampled from correct thermal distribution |
| 🔵 **3D Visualization** | Real-time interactive 3D plot — D (red), T (blue), He-4 (green▲), n (gray■) |
| 📊 **Data Analysis** | Live reaction table with rate, probability, `<σv>`, energy per event |
| 📈 **Statistics Panel** | Comprehensive physics metrics, efficiency, FPS monitoring |
| 💾 **Save / Load** | Export data as JSON or CSV, export 3D plot as PNG/PDF |
| 🎛️ **Live Controls** | Adjust temperature (10⁷–2×10⁸ K) and density in real time |

---

## 🚀 Quick Start

### 1. Clone
```bash
git clone https://github.com/Hayder-IRAQ/nuclear-fusion-sim.git
cd nuclear-fusion-sim
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
python main.py
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `numpy` | Particle arrays, physics calculations |
| `matplotlib` | 3D visualization, plot export |
| `pandas` | Data analysis, CSV export |
| `tkinter` | GUI *(built into Python — no install needed)* |

---

## 🎛️ How to Use

1. **Start** — Click "Start Simulation" to begin
2. **Temperature** — Slide to change plasma temperature (higher = more reactions)
3. **Density** — Slide to change particle density
4. **Speed** — Control simulation speed (0.1× to 5×)
5. **Pause / Resume** — Pause at any time
6. **Data tab** — View per-reaction data table
7. **Statistics tab** — View aggregated physics metrics
8. **File → Save Data** — Export to JSON or CSV
9. **File → Export Plot** — Save 3D snapshot

---

## 🧪 Physics Parameters

| Parameter | Default Value | Description |
|---|---|---|
| Temperature | 1×10⁸ K (8.6 keV) | Plasma temperature |
| Density | 1×10²⁰ m⁻³ | Particle number density |
| Time step | 1×10⁻¹² s (1 ps) | Simulation time resolution |
| Volume | 1×10⁻²¹ m³ | Simulation box size |
| D particles | 100 | Initial deuterium count |
| T particles | 100 | Initial tritium count |

---

## 📐 Statistical Model Details

For each deuterium particle at each time step:

```python
reaction_rate     = n_tritium * sigma_v          # s⁻¹
fusion_probability = 1 - exp(-reaction_rate * dt) # dimensionless
if random() < fusion_probability:
    # fusion event occurs
    consume D + T → produce He-4 + neutron
```

Where `sigma_v` is computed via **Bosch-Hale (1992)** parameterization — the same formula used in ITER and tokamak design calculations.

---

## 📊 Output Data Fields

Each fusion event records:

| Field | Description |
|---|---|
| `step` | Simulation step number |
| `time_ns` | Simulation time in nanoseconds |
| `temperature_kev` | Plasma temperature in keV |
| `reaction_rate` | Instantaneous reaction rate (s⁻¹) |
| `fusion_probability` | Event probability (%) |
| `sigma_v_m3s` | Reaction rate coefficient `<σv>` (m³/s) |
| `energy_released_mev` | Energy per reaction (17.6 MeV) |
| `total_energy_mev` | Cumulative energy released |

---

## 🗂️ Project Structure

```
nuclear-fusion-sim/
├── main.py          # Full simulation (single file)
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🤝 Contributing

Contributions welcome! Ideas for improvement:
- Add magnetic confinement (tokamak geometry)
- Add D-D and D-He3 reaction channels
- Add energy balance (Q-factor calculation)
- Add particle loss mechanisms

1. Fork → feature branch → PR

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Hayder Odhafa / حيدر عذافة**
GitHub: [@Hayder-IRAQ](https://github.com/Hayder-IRAQ)

---

<div align="center">

**⚛️ Simulated Reaction: ²H + ³H → ⁴He + ¹n + 17.6 MeV**

*Made with ❤️ and Python — Nuclear Fusion Simulation v4.0 © 2025 Hayder Odhafa*

</div>
