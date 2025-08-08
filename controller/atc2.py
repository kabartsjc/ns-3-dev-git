import time
import bluesky as bs
from bluesky.core import Base
from bluesky.network import subscriber
from bluesky.network.client import Client
from bluesky.stack import stack
from geoutils import geo  # Usa sua função de distância personalizada


class AircraftInfoCollector(Base):
    def __init__(self):
        super().__init__()
        self.aircraft = {}

    @subscriber
    def acdata(self, data):
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


def detect_and_resolve_conflicts(aircraft_data):
    ids = list(aircraft_data.keys())

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            ac1_id = ids[i]
            ac2_id = ids[j]
            ac1 = aircraft_data[ac1_id]
            ac2 = aircraft_data[ac2_id]

            alt_diff = abs(ac1['alt'] - ac2['alt'])
            horiz_dist = geo.distance_haversine(ac1['lat'], ac1['lon'], ac2['lat'], ac2['lon'])

            if alt_diff < 1000 and horiz_dist < 5:
                print(f"[{time.strftime('%H:%M:%S')}] [CONFLICT] {ac1_id} vs {ac2_id} | "
                      f"alt_diff={alt_diff:.1f} ft, dist={horiz_dist:.2f} NM")

                new_alt_1 = max(1000, min(45000, int(ac1['alt'] + 1000)))
                new_alt_2 = max(1000, min(45000, int(ac2['alt'] - 1000)))

                # ✅ Formato que FUNCIONA no seu ambiente: <CALLSIGN> ALT <VALUE>
                cmd1 = f"{ac1_id} ALT {new_alt_1}"
                cmd2 = f"{ac2_id} ALT {new_alt_2}"

                print(f"[DEBUG] Enviando: {cmd1}")
                print(f"[DEBUG] Enviando: {cmd2}")

                stack(cmd1)
                stack(cmd2)


def main():
    bs.init(mode='client')
    client = Client()
    client.connect()
    print("[INFO] AI ATC Client with Conflict Resolution started")

    aircraft_info_collector = AircraftInfoCollector()

    # ✅ Comando de teste para validar que o stack está ativo
    #stack("ABC17 ALT 6000")  # <- substitua por callsign válido no seu cenário

    while True:
        client.update()

        aircraft_data = aircraft_info_collector.get_all_aircraft()
        if len(aircraft_data) >= 2:
            detect_and_resolve_conflicts(aircraft_data)

        time.sleep(1)


if __name__ == "__main__":
    main()
