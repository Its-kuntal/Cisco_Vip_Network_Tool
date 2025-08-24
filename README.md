# 🚀 Cisco VIP 2025 – Complete Network Analysis & Simulation Tool

### 📌 Overview

This project was developed as part of the **Cisco Virtual Internship Program 2025 – Networking Stream**.
It provides a **comprehensive tool** to parse device configurations, automatically construct a hierarchical network topology, validate configurations, and simulate real-world scenarios with fault injection and recovery.

---

## ✨ Features

* **🔹 Topology Generation**

  * Automatic creation of hierarchical network topology from router & switch configs.
  * Interactive visualization of the generated network (HTML + PNG).

* **🔹 Validation & Optimization**

  * Detection of missing components (e.g., endpoints not connected).
  * Duplicate IP, VLAN consistency, gateway verification.
  * MTU mismatch and loop detection.
  * Routing protocol recommendations (e.g., BGP vs. OSPF).

* **🔹 Performance & Load Analysis**

  * Bandwidth capacity validation for each link.
  * Load balancing recommendations for high-traffic scenarios.

* **🔹 Simulation & Fault Injection**

  * **Day-1 Simulation:** Device bring-up, ARP, OSPF, BGP.
  * **Day-2 Testing:** 40+ functional tests with pass/fail summary.
  * Link failure & recovery simulation.
  * Pause/resume capability for dynamic testing.

* **🔹 Implementation Highlights**

  * Multithreaded node representation (routers, switches, PCs).
  * Inter-process communication (IPC) using TCP/IP.
  * Per-node logging and statistics.
  * Comprehensive reports (JSON + HTML + visual diagrams).

---

## 📂 Project Structure

```
CISCO-VIP-NETWORKING-2025/
│── .venv/                      # Virtual environment
│── comprehensive_reports/      # Generated reports & visualizations
│── configs/                    # Device configuration files (PCs, Routers, Switches)
│   ├── PC1.txt ... PC6.txt
│   ├── R1.txt, R2.txt, R3.txt
│   ├── S1.txt, S2.txt, S3.txt
│
│── src/
│   ├── __init__.py
│   ├── cisco_parser.py         # Parser for Cisco configs
│   ├── day1_simulation.py      # Day-1 simulation engine
│   ├── day2_testing.py         # Day-2 test cases
│   ├── main_integration.py     # Main entry point
│   ├── network_validator.py    # Validation logic
│   ├── simulation_engine.py    # Fault injection & engine
│   ├── topology_builder.py     # Builds logical topology
│   ├── topology_renderer.py    # Renders interactive/visual topology
│   ├── traffic_analyzer.py     # Performance & load analysis
│
│── requirements.txt            # Python dependencies
│── README.md                   # Project documentation
```

---

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Its-kuntal/Cisco_Vip_Network_Tool
   ```

2. **Create virtual environment & install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # (Linux/Mac)
   .venv\Scripts\activate      # (Windows)

   pip install -r requirements.txt
   ```

---

## ▶️ Usage

Run the complete analysis tool:

```bash
python src/main_integration.py
```

For quick testing with sample configs:

```bash
python src/runner.py
```

---

## 📊 Sample Output

* **Parsed Configurations:** 12
* **Topology Constructed:** 12 nodes, 21 links
* **Day-2 Test Summary:** 46 tests executed, 46 passed ✅
* **Compliance Summary:** Fully meets Cisco VIP 2025 requirements

Generated outputs:

* **Main Report:** `comprehensive_reports/comprehensive_analysis_<timestamp>.json`
* **Interactive Topology:** `comprehensive_reports/network_topology_<timestamp>.html`
* **Visual Diagram:** PNG image included in reports

---

## 📌 Internship Requirement Compliance

✔️ Hierarchical topology construction
✔️ Bandwidth and capacity verification
✔️ Load balancing recommendations
✔️ Missing component detection
✔️ Configuration validation (IP, VLAN, MTU, loops)
✔️ Day-1 and Day-2 simulations
✔️ Fault injection & recovery
✔️ Multithreaded IPC-based simulation

---

## 🏆 Conclusion

This tool provides a **one-stop solution** for automated **network topology generation, validation, and simulation**, fully aligned with the **Cisco Virtual Internship Program 2025 – Networking Stream** requirements.
