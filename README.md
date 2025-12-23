# 🛬 Landing Gear Digital Twin Architecture
### Next-generation predictive maintenance suite. Bridging the gap between physical strut dynamics and digital telemetry to eliminate reactive maintenance in landing gear operations.

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a-orange?style=for-the-badge&logo=mathworks)
![Simulink](https://img.shields.io/badge/Simulink-Model-blue?style=for-the-badge&logo=mathworks)
![Status](https://img.shields.io/badge/Status-Active_Research-green?style=for-the-badge)

## 📡 Mission Overview
This project develops a **High-Fidelity Digital Twin** of an aircraft landing gear system. Unlike traditional maintenance which relies on scheduled intervals, this model uses real-time physics simulation to predict component health.

By modeling the internal gas thermodynamics and hydraulic damping forces in **Simulink**, we can compare "Ideal" vs "Actual" strut performance to detect:
* Gas leakage (Nitrogen charge pressure drop).
* Hydraulic fluid degradation.
* Seal friction wear and tear.

graph TD
    subgraph "Node A: Flight Management System"
        Python[High_Fidelity_Aircraft.py] -->|Generates Telemetry| UDP_Out[UDP Stream]
        Python -->|Injects Faults| DB[(PostgreSQL)]
    end

    subgraph "Node B: Digital Twin Physics"
        DB -->|Polls Phase Change| MATLAB[AeroTwin_Master_Console.m]
        MATLAB -->|Updates k/b| Simulink[Fancy_Landing_Gear.slx]
        Simulink -->|Solves Dynamics| Simscape[3D Multibody Physics]
    end

    subgraph "Node C: Telemetry Pipeline"
        UDP_Out -->|Visuals| FlightGear[FlightGear 3D]
        UDP_Out -->|Metrics| Telegraf[Telegraf Agent]
        Telegraf -->|Storage| Influx[InfluxDB 3 Core]
        Influx -->|Dashboard| Grafana[Grafana Monitor]
    end

    style Python fill:#3776AB,stroke:#fff,color:#fff
    style MATLAB fill:#e16737,stroke:#fff,color:#fff
    style Simulink fill:#0076A8,stroke:#fff,color:#fff
    style Influx fill:#22ADF6,stroke:#fff,color:#fff
    
## 🛠️ Technical Architecture

### 1. The Physics Model
The simulation solves the dynamic equation of motion for the Oleo-Pneumatic strut:

$$F_{total} = F_{gas} + F_{damp} + F_{friction}$$

Where:
* **F_gas:** Calculated using Polytropic gas laws ($P V^n = C$).
* **F_damp:** Velocity-squared damping based on orifice diameter.
* **F_friction:** Stribeck effect friction modeling for seal analysis.

### 2. Simulation Environment
* **Tool:** MATLAB / Simulink
* **Input:** Vertical velocity at touchdown ($V_z$), Aircraft Mass.
* **Output:** Strut compression, internal pressure, seal wear index.

## 📂 Repository Structure

```text
├── 📁 Models/           # The core Simulink (.slx) files
│   ├── main_gear.slx    # Primary physics model
│   └── seal_friction.slx # Sub-system for friction analysis
├── 📁 Scripts/          # MATLAB (.m) initialization scripts
│   ├── init_params.m    # Loads constants (Gas area, Oil volume)
│   └── plot_results.m   # Generates graphs from simulation data
├── 📁 Docs/             # Technical diagrams and equations
└── README.md            # You are here
