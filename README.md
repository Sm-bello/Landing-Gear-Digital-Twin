# 🛬 High-Fidelity Landing Gear Digital Twin
### Next-Generation Cyber-Physical System (CPS) for Predictive Maintenance

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a-orange?style=for-the-badge&logo=mathworks)
![Simulink](https://img.shields.io/badge/Simulink-Simscape_Multibody-blue?style=for-the-badge&logo=mathworks)
![Python](https://img.shields.io/badge/Python-Flight_Dynamics-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_Research-2ea44f?style=for-the-badge)

## 📡 Mission Overview
This project develops a **Cyber-Physical System (CPS)** architecture for aircraft landing gear operations. Unlike traditional simulations that exist in a vacuum, this Digital Twin integrates a **Physics-Based Plant** (Simscape Multibody) with an autonomous **Flight Management System** (Python) to simulate realistic operational stressors.

By bridging the gap between **Operational Technology (OT)** and **Information Technology (IT)**, this system enables:
* **Real-time Fault Injection:** Simulating hard landings (>2.5G) and seal degradation.
* **Predictive Analytics:** Forecasting oleo-pneumatic strut failure before airworthiness is compromised.
* **Telemetry Streaming:** Broadcasting flight data via UDP to InfluxDB 3 and Grafana.

---

## 🏗️ System Architecture

The system operates as a distributed network of three synchronized nodes:

```mermaid
graph TD
    subgraph "Node A: Flight Management System"
        Python[High_Fidelity_Aircraft.py] -->|Generates Telemetry| UDP_Out[UDP Stream]
        Python -->|Injects Faults| DB[(PostgreSQL)]
    end

    subgraph "Node B: Digital Twin Plant"
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
