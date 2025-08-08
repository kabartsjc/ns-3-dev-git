
from bluesky import stack, sim
from bluesky.tools import geo
from datetime import datetime
import time

class AircraftCollector:
    def get_all_aircraft(self):
        aircraft_data = {}
        for ac in sim.traffic:
            aircraft_data[ac.id] = {
                'lat': ac.lat,
                'lon': ac.lon,
                'alt': ac.alt,
                'hdg': ac.trk,
                'dest': ac.dest if hasattr(ac, 'dest') else None
            }
        return aircraft_data

class ICAOSeparationController:
    def __init__(self, collector):
        self.collector = collector
        self.min_horizontal_sep = 5.0  # NM
        self.min_vertical_sep = 1000  # ft

    def enforce_separation(self):
        aircraft_data = self.collector.get_all_aircraft()
        ids = list(aircraft_data.keys())

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                id1, id2 = ids[i], ids[j]
                ac1, ac2 = aircraft_data[id1], aircraft_data[id2]

                horizontal_distance = geo.distance_haversine(ac1['lat'], ac1['lon'], ac2['lat'], ac2['lon'])
                vertical_distance = abs(ac1['alt'] - ac2['alt'])

                if horizontal_distance < self.min_horizontal_sep and vertical_distance < self.min_vertical_sep:
                    print(f"[{datetime.utcnow().isoformat()}Z] Conflito entre {id1} e {id2}: "
                          f"{horizontal_distance:.2f} NM horizontal / {vertical_distance:.0f} ft vertical")
                    
                    # Estratégia: subir a aeronave com menor altitude
                    if ac1['alt'] < ac2['alt']:
                        stack(f"{id1} ALT {ac1['alt'] + 1000}")
                        print(f"[INFO] {id1} subindo para evitar conflito")
                    else:
                        stack(f"{id2} ALT {ac2['alt'] + 1000}")
                        print(f"[INFO] {id2} subindo para evitar conflito")

    def remove_arrived_aircraft(self):
        aircraft_data = self.collector.get_all_aircraft()
        for ac_id, ac in aircraft_data.items():
            if not ac['dest']:
                continue

            try:
                dest_parts = ac['dest'].split(',')
                if len(dest_parts) != 2:
                    continue
                dest_lat = float(dest_parts[0])
                dest_lon = float(dest_parts[1])
            except ValueError:
                continue

            distance = geo.distance_haversine(ac['lat'], ac['lon'], dest_lat, dest_lon)
            if distance < 2.0 and ac['alt'] < 1000:
                print(f"[INFO] Removendo {ac_id}: chegou ao destino ({distance:.2f} NM)")
                stack(f"{ac_id} DEL")

def main():
    print(f"[{datetime.utcnow().isoformat()}Z] ICAO-based ATC controller started.")
    collector = AircraftCollector()
    controller = ICAOSeparationController(collector)

    while True:
        controller.enforce_separation()
        controller.remove_arrived_aircraft()
        time.sleep(1)

if __name__ == '__main__':
    main()
