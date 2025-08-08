import time
import bluesky as bs
from bluesky.core import Base
from bluesky.network import subscriber
from bluesky.network.client import Client
from bluesky.stack import stack
from geoutils import geo  # Uses your custom haversine distance function


# --- Separation standards based on ICAO Doc 4444, Annex 11, and DECEA ICA 100-37 ---
class SeparationStandards:
    VERTICAL_MIN = 1000  # Vertical separation minimum in feet (RVSM: FL290 to FL410)
    LATERAL_MIN_RADAR = 5  # Lateral separation in nautical miles when using radar
    ALTITUDE_LIMITS = (1000, 45000)  # Minimum and maximum operational altitudes (ft)


# --- Aircraft data subscriber ---
class AircraftInfoCollector(Base):
    def __init__(self):
        super().__init__()
        self.aircraft = {}

    @subscriber
    def acdata(self, data):
        # Update the internal dictionary with the latest aircraft state data
        self.aircraft.clear()
        for i in range(len(data.id)):
            ac_id = data.id[i].strip()
            self.aircraft[ac_id] = {
                'lat': data.lat[i],
                'lon': data.lon[i],
                'alt': data.alt[i],
                'tas': data.tas[i],
                'gs': data.gs[i],
                'vs': data.vs[i],
                'dest': data.dest[i] if hasattr(data, 'dest') else '',
            }

    def get_all_aircraft(self):
        return self.aircraft


# --- ICAO-compliant separation logic ---
class ICAOSeparationController:
    def __init__(self, collector):
        self.collector = collector
        self.assigned_altitudes = {}  # Tracks assigned altitudes per callsign
        self.cooldowns = {}  # Tracks last command timestamps per callsign
        self.COOLDOWN_SEC = 20  # Cooldown period in seconds before reissuing a command

    def enforce_separation(self):
        aircraft_data = self.collector.get_all_aircraft()
        ids = list(aircraft_data.keys())

        # Compare all unique pairs of aircraft
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                self._evaluate_pair(ids[i], ids[j], aircraft_data)

    def _evaluate_pair(self, ac1_id, ac2_id, data):
        ac1 = data[ac1_id]
        ac2 = data[ac2_id]

        alt_diff = abs(ac1['alt'] - ac2['alt'])
        dist = geo.distance_haversine(ac1['lat'], ac1['lon'], ac2['lat'], ac2['lon'])

        # Check against ICAO separation minima
        if alt_diff < SeparationStandards.VERTICAL_MIN and dist < SeparationStandards.LATERAL_MIN_RADAR:
            print(f"[{time.strftime('%H:%M:%S')}] [CONFLICT] {ac1_id} vs {ac2_id} | ",
                  f"alt_diff={alt_diff:.1f} ft, dist={dist:.2f} NM")

            self._issue_resolution(ac1_id, ac2_id, ac1['alt'], ac2['alt'])

    def _issue_resolution(self, ac1_id, ac2_id, alt1, alt2):
        now = time.time()
        new_alt1 = max(SeparationStandards.ALTITUDE_LIMITS[0], min(SeparationStandards.ALTITUDE_LIMITS[1], int(alt1 + 1000)))
        new_alt2 = max(SeparationStandards.ALTITUDE_LIMITS[0], min(SeparationStandards.ALTITUDE_LIMITS[1], int(alt2 - 1000)))

        if not self._on_cooldown(ac1_id, now) and not self._already_assigned_and_reached(ac1_id, new_alt1, alt1):
            cmd1 = f"{ac1_id} ALT {new_alt1}"
            print(f"[RESOLVE] {cmd1}")
            stack(cmd1)
            self.assigned_altitudes[ac1_id] = new_alt1
            self.cooldowns[ac1_id] = now

        if not self._on_cooldown(ac2_id, now) and not self._already_assigned_and_reached(ac2_id, new_alt2, alt2):
            cmd2 = f"{ac2_id} ALT {new_alt2}"
            print(f"[RESOLVE] {cmd2}")
            stack(cmd2)
            self.assigned_altitudes[ac2_id] = new_alt2
            self.cooldowns[ac2_id] = now

    def _already_assigned_and_reached(self, callsign, target_alt, current_alt):
        if callsign not in self.assigned_altitudes:
            return False
        assigned = self.assigned_altitudes[callsign]
        if assigned != target_alt:
            return False
        return abs(current_alt - target_alt) < 100  # Consider reached if within 100 ft tolerance

    def _on_cooldown(self, callsign, now):
        return callsign in self.cooldowns and (now - self.cooldowns[callsign] < self.COOLDOWN_SEC)


# --- Main execution loop ---
def main():
    bs.init(mode='client')
    client = Client()
    client.connect()
    print("[INFO] ICAO-based ATC Controller started")

    collector = AircraftInfoCollector()
    controller = ICAOSeparationController(collector)

    while True:
        client.update()
        controller.enforce_separation()
        time.sleep(1)


if __name__ == "__main__":
    main()
