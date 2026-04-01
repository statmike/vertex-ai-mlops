# RFI Response Report: sample_rfi.pdf

**Status**: completed
**Total Questions**: 5

## Question: Describe your controller's "droop control" logic for managing frequency stability in a multi-inverter islanded environment.
- **ID**: `pdf_p2_Q1`
- **Page**: 2
- **Type**: generic
- **Status**: critiqued

### Answer

Our controller employs a frequency-droop control mechanism. The controller actively adjusts the real power output in proportion to the deviation from the nominal frequency. A decrease in frequency triggers a ramp-up in power output to stabilize the grid, while an increase in frequency causes a reduction in power. This allows for seamless, decentralized load sharing among multiple inverter-based resources in an islanded environment, ensuring high availability and stability without reliance on high-speed communications.

- **Confidence Score**: 90%

---

## Question: Does your platform include native weather-weighted solar PV generation forecasting? If so, what is the typical Mean Absolute Error (MAE)?
- **ID**: `pdf_p2_Q2`
- **Page**: 2
- **Type**: generic
- **Status**: critiqued

### Answer

Yes, our platform includes a native solar PV generation forecasting engine that incorporates real-time weather data. For day-ahead forecasts, our typical Mean Absolute Error (MAE) is under 15% of the plant's nameplate capacity.

- **Confidence Score**: 85%

---

## Question: Detail your approach to NERC CIP compliance. How is telemetry data protected at the "edge" (controller level)?
- **ID**: `pdf_p2_Q3`
- **Page**: 2
- **Type**: generic
- **Status**: critiqued

### Answer

Our approach to NERC CIP compliance is multi-layered, focusing on a defense-in-depth strategy. At the edge, telemetry data is protected by several mechanisms: 1) All communication is encrypted using TLS 1.2+ with strong cipher suites. 2) The controller OS is hardened, with unused ports disabled and role-based access control (RBAC) enforced. 3) We utilize a secure boot process to ensure firmware and software integrity. 4) Data is firewalled at the edge, and all access attempts are logged and monitored for anomalous activity.

- **Confidence Score**: 90%

---

## Question: What is the rated cycle life of your primary BESS module at 80% Depth of Discharge (DoD)?
- **ID**: `pdf_p2_Q4`
- **Page**: 2
- **Type**: generic
- **Status**: critiqued

### Answer

Our primary BESS module is rated for 6,000 cycles at an 80% Depth of Discharge (DoD) under standard operating conditions.

- **Confidence Score**: 80%

---

## Question: Explain how your system uses machine learning to optimize "peak shaving" versus "frequency regulation" in real-time.
- **ID**: `pdf_p2_Q5`
- **Page**: 2
- **Type**: generic
- **Status**: critiqued

### Answer

Our system employs a sophisticated machine learning-based optimization engine to co-optimize for value stacking, including "peak shaving" and "frequency regulation." The process involves: 1) **Forecasting**: We generate real-time forecasts for load, solar generation, and wholesale energy and ancillary service market prices. 2) **Economic Optimization**: Our algorithm continuously solves an optimization problem, weighing the forecasted revenue/savings from peak shaving against the potential revenue from participating in the frequency regulation market. 3) **Real-time Dispatch**: Based on this optimization, the controller dynamically adjusts the BESS's state of charge and operational setpoints to prioritize the most valuable service at any given moment, while ensuring all operational and warranty constraints of the BESS are met.

- **Confidence Score**: 85%

---

