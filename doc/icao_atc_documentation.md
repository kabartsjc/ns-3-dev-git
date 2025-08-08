# ICAO-Based ATC Controller

**Filename:** `icao_atc.py`  
**Generated on:** 2025-08-07 23:27:29

This Python script implements an ICAO-compliant Air Traffic Control (ATC) controller for use with the BlueSky simulator. It monitors aircraft state data, detects potential conflicts based on ICAO separation standards, and issues altitude changes to maintain safe separation.

---

## ✈️ Functional Overview

### 1. `SeparationStandards`
Defines ICAO-standard separation minima and altitude limits:
- **Vertical separation:** 1000 ft
- **Lateral (radar-based) separation:** 5 NM
- **Operational altitude range:** 1000–45000 ft

---

### 2. `AircraftInfoCollector` (inherits from `Base`)
Responsible for collecting and storing real-time aircraft data.
- **acdata(data)**: Subscribed method that processes aircraft telemetry (id, lat, lon, alt, etc.)
- **get_all_aircraft()**: Returns dictionary with all active aircraft states

---

### 3. `ICAOSeparationController`
The core class for conflict detection and resolution.

#### Key Components:
- **`enforce_separation()`**: Iterates over all aircraft pairs and identifies conflicts using future position prediction.
- **`_evaluate_pair()`**: Projects aircraft positions into the future and checks if separation is violated.
- **`_issue_resolution()`**: Sends altitude change commands using BlueSky `stack()` API to resolve detected conflicts.
- **`_project_position()`**: Projects a future position based on TAS, heading, and elapsed time.
- **`_already_assigned_and_reached()`**: Avoids reissuing altitude change commands that were already applied.
- **`_on_cooldown()`**: Prevents command spamming with a cooldown mechanism.

#### Conflict Resolution:
- Assigns new altitudes (±1000 ft) to conflicting aircraft.
- Uses `stack("<CALLSIGN> ALT <ALTITUDE>")` to send ATC instructions.

---

### 4. `main()`
- Initializes BlueSky in client mode and connects via `Client()`.
- Instantiates collector and controller.
- Enters an infinite loop to:
  - Update aircraft states
  - Detect and resolve conflicts every second

---

## 📤 Future Extensions

- Add horizontal speed constraints or turning maneuvers
- Detect destination arrival and delete aircraft using `stack("DEL <CALLSIGN>")`
- Integrate voice ATC command logs or visualization overlays

---

## 🔧 Dependencies

- `bluesky` (BlueSky simulator)
- `geoutils.geo` (Custom module for great-circle distance calculation)

---

## 📜 Logging Behavior

- Logs predicted conflicts with alt/lateral distances
- Logs every command sent to aircraft (ALT changes)

---

## 📌 Notes

- This version supports **conflict prediction (60s lookahead)**.
- Altitude changes are bounded by ICAO altitude limits.
- Aircraft not reaching assigned altitudes are considered in future cycles.

