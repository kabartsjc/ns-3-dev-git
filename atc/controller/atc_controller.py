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
    

class ICAOSeparationController:
    def __init__(self, collector):
        self.collector = collector
        self.assigned_altitudes = {}  # Tracks assigned altitudes per callsign
        self.cooldowns = {}  # Tracks last command timestamps per callsign
        self.COOLDOWN_SEC = 20  # Cooldown period in seconds before reissuing a command
        self.LOOKAHEAD_SEC = 60  # Prediction window (in seconds)
        self.net = AtcNetwork("config/sensores.json")



# --- Main execution loop ---
def main():
    bs.init(mode='client')
    client = Client()
    client.connect()
    print("[INFO] ICAO-based ATC Controller with Conflict Prediction started")
# --- Main execution loop ---
def main():
    bs.init(mode='client')
    client = Client()
    client.connect()
    print("[INFO] ICAO-based ATC Controller with Conflict Prediction started")

    log = open("events.log.jsonl","a")




