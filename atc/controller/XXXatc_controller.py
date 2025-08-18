import time
import math
import bluesky as bs
from bluesky.core import Base
from bluesky.network import subscriber
from bluesky.network.client import Client
from bluesky.stack import stack
from atc.utils.geoutils import geo  # Uses your custom haversine distance function
from atc.net.network_model import AtcNetwork
from atc.utils.logs.logging_utils import log_event

# --- Separation standards based on ICAO Doc 4444, Annex 11, and DECEA ICA 100-37 ---
class SeparationStandards:
    VERTICAL_MIN = 1000  # Vertical separation minimum in feet (RVSM: FL290 to FL410)
    LATERAL_MIN_RADAR = 5  # Lateral separation in nautical miles when using radar
    ALTITUDE_LIMITS = (1000, 45000)  # Minimum and maximum operational altitudes (ft)

    # Critérios de remoção (ajuste conforme necessário)
    REMOVAL_RADIUS_NM = 2.0
    REMOVAL_ALTITUDE_FT = 1000


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
                'hdg': data.hdg[i] if hasattr(data, 'hdg') else 0,
                'dest': data.dest[i] if hasattr(data, 'dest') else '',
            }

    def get_all_aircraft(self):
        return self.aircraft


# --- ICAO-compliant separation logic with prediction and prioritization ---
class ICAOSeparationController:
    def __init__(self, collector):
        self.collector = collector
        self.assigned_altitudes = {}  # Tracks assigned altitudes per callsign
        self.cooldowns = {}  # Tracks last command timestamps per callsign
        self.COOLDOWN_SEC = 20  # Cooldown period in seconds before reissuing a command
        self.LOOKAHEAD_SEC = 60  # Prediction window (in seconds)

    def enforce_separation(self):
        aircraft_data = self.collector.get_all_aircraft()
        ids = list(aircraft_data.keys())

        conflict_queue = []

        # Compare all unique pairs of aircraft
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                conflict = self._evaluate_pair(ids[i], ids[j], aircraft_data)
                if conflict:
                    conflict_queue.append(conflict)

        # Prioritize by severity (closest and lowest vertical sep first)
        conflict_queue.sort(key=lambda c: (c['h_dist'], c['v_dist']))
        for conflict in conflict_queue:
            self._issue_resolution(**conflict)

    def _evaluate_pair(self, ac1_id, ac2_id, data):
        ac1 = data[ac1_id]
        ac2 = data[ac2_id]

        # Predict future positions and altitudes
        lat1, lon1 = self._project_position(ac1['lat'], ac1['lon'], ac1['tas'], ac1['hdg'], self.LOOKAHEAD_SEC)
        lat2, lon2 = self._project_position(ac2['lat'], ac2['lon'], ac2['tas'], ac2['hdg'], self.LOOKAHEAD_SEC)

        alt1 = ac1['alt'] + (ac1['vs'] * self.LOOKAHEAD_SEC / 60)
        alt2 = ac2['alt'] + (ac2['vs'] * self.LOOKAHEAD_SEC / 60)

        alt_diff = abs(alt1 - alt2)
        dist = geo.distance_haversine(lat1, lon1, lat2, lon2)

        if alt_diff < SeparationStandards.VERTICAL_MIN and dist < SeparationStandards.LATERAL_MIN_RADAR:
            print(f"[{time.strftime('%H:%M:%S')}] [PREDICTED CONFLICT] {ac1_id} vs {ac2_id} | ",
                  f"alt_diff={alt_diff:.1f} ft, dist={dist:.2f} NM")
            return {
                'ac1_id': ac1_id,
                'ac2_id': ac2_id,
                'alt1': ac1['alt'],
                'alt2': ac2['alt'],
                'h_dist': dist,
                'v_dist': alt_diff
            }
        return None

    def _issue_resolution(self, ac1_id, ac2_id, alt1, alt2, **_):
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

    def _project_position(self, lat, lon, tas, heading, delta_seconds):
        # Estimate future position assuming constant TAS and heading (great-circle projection)
        R = 3440.065  # Earth radius in NM
        d = (tas * delta_seconds) / 3600  # Distance in NM

        rad = math.radians
        deg = math.degrees

        lat1 = rad(lat)
        lon1 = rad(lon)
        hdg = rad(heading)

        lat2 = math.asin(math.sin(lat1) * math.cos(d / R) +
                         math.cos(lat1) * math.sin(d / R) * math.cos(hdg))

        lon2 = lon1 + math.atan2(math.sin(hdg) * math.sin(d / R) * math.cos(lat1),
                                 math.cos(d / R) - math.sin(lat1) * math.sin(lat2))

        return deg(lat2), deg(lon2)
    
 
    def remove_aircraft_arrived(self):
        aircraft_data = self.collector.get_all_aircraft()
        
        for acid, ac in aircraft_data.items():
            # Verifica se destino está definido
            if 'destx' not in ac or 'desty' not in ac or ac['destx'] is None or ac['desty'] is None:
                continue

            # Cálculo da distância 2D
            dx = ac['destx'] - ac['x']
            dy = ac['desty'] - ac['y']
            dist_nm = (dx**2 + dy**2) ** 0.5

            # Altitude
            alt_ft = ac.get('alt', 99999)

            if dist_nm < 2.0 and alt_ft < 1000:
                print(f"[INFO] DEL {acid} — aircraft arrived at destination.")
                stack.stackcmd(f"DEL {acid}")



# --- Main execution loop ---
def main():
    bs.init(mode='client')
    client = Client()
    client.connect()
    print("[INFO] ICAO-based ATC Controller with Conflict Prediction started")

    net = AtcNetwork("config/sensores.json")
    log = open("events.log.jsonl","a")



    collector = AircraftInfoCollector()
    controller = ICAOSeparationController(collector)

    while True:
        client.update()
        controller.enforce_separation()
        controller.remove_aircraft_arrived()
        time.sleep(1)


if __name__ == "__main__":
    main()
