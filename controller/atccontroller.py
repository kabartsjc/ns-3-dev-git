import time
import math
import bluesky as bs
from bluesky.core import Base
from bluesky.network import subscriber
from bluesky.network.client import Client
from bluesky.stack import stack
from geoutils import geo



class AircraftInfoCollector(Base):
    def __init__(self):
        super().__init__()
        self.aircraft = {}

    @subscriber
    def acdata(self, data):
        self.aircraft.clear()
        for i in range(len(data.id)):
            ac_id = data.id[i]
            self.aircraft[ac_id] = {
                'lat': data.lat[i],
                'lon': data.lon[i],
                'alt': data.alt[i],
                'tas': data.tas[i],
                'gs': data.gs[i],
                'vs': data.vs[i],
                'dest': data.dest[i] if hasattr(data, 'dest') else '',
            }

    def get_aircraft(self, ac_id):
        return self.aircraft.get(ac_id, None)

    def get_all_aircraft(self):
        return self.aircraft


def detect_and_resolve_conflicts(aircraft_data):
    ids = list(aircraft_data.keys())

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            ac1 = aircraft_data[ids[i]]
            ac2 = aircraft_data[ids[j]]

            alt_diff = abs(ac1['alt'] - ac2['alt'])
            horiz_dist = geo.haversine_nm(ac1['lat'], ac1['lon'], ac2['lat'], ac2['lon'])

            if alt_diff < 1000 and horiz_dist < 5:
                print(f"[CONFLICT] Between {ids[i]} and {ids[j]}: alt_diff={alt_diff} ft, dist={horiz_dist:.2f} NM")

                # Resolve: climb one and descend the other
                new_alt_1 = int(ac1['alt'] + 1000)
                new_alt_2 = int(ac2['alt'] - 1000)

                print(f"[RESOLVE] Command: {ids[i]} ALT {new_alt_1}")
                print(f"[RESOLVE] Command: {ids[j]} ALT {new_alt_2}")

                stack(f"ALT {ids[i]} {new_alt_1}")
                stack(f"ALT {ids[j]} {new_alt_2}")


def main():
    bs.init(mode='client')
    client = Client()
    client.connect()
    print("[INFO] AI ATC Client with Conflict Resolution started")

    aircraft_info_collector = AircraftInfoCollector()

    while True:
        client.update()

        aircraft_data = aircraft_info_collector.get_all_aircraft()
        if len(aircraft_data) >= 2:
            detect_and_resolve_conflicts(aircraft_data)

        time.sleep(1)


if __name__ == "__main__":
    main()
