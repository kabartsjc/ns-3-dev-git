import json, random, time
from atc.utils.geoutils import distance_haversine

class AtcNetwork:
    def __init__(self, sensores_json):
        self.cfg = json.load(open(sensores_json,"r"))
        self.c = self.cfg["channel"]["c"]
        self.controller = self.cfg["controller"]
        self.adsb = self.cfg["adsb_stations"]
        self.radars = self.cfg["radars"]
        self.ch = self.cfg["channel"]

    # atraso de propagação em ms
    def _prop_delay_ms(self, lat1,lon1,lat2,lon2):
        d_km = distance_haversine(lat1,lon1,lat2,lon2)
        d_m  = d_km*1000
        return 1000.0 * (d_m / self.c)

    # ADS-B: aeronave -> estação -> controlador
    def adsb_delay_model(self, ac):
        lat, lon = ac["lat"], ac["lon"]
        vis = []
        for s in self.adsb:
            if distance_haversine(lat,lon,s["lat"],s["lon"]) <= s["rx_range_km"]:
                vis.append(s)
        if not vis:
            return None  # fora de cobertura

        s = min(vis, key=lambda st: distance_haversine(lat,lon,st["lat"],st["lon"]))
        air2gs = self._prop_delay_ms(lat,lon,s["lat"],s["lon"])
        gs2ctrl = self._prop_delay_ms(s["lat"],s["lon"],self.controller["lat"],self.controller["lon"])
        base = s["base_delay_ms"] + self.ch["controller_proc_ms"]
        jitter = random.uniform(-s["jitter_ms"], s["jitter_ms"])
        per = s["loss"]
        return {
            "station": s["id"],
            "delay_ms": max(0.0, base + air2gs + gs2ctrl + jitter),
            "loss": (random.random() < per),
            "period_s": self.ch["adsb_air_tx_period_s"]
        }

    # Radar: gera “ticks” de atualização com prob. detecção e atraso
    def radar_observation(self, ac, last_update_t, now_t):
        # só atualiza no múltiplo de update_s
        upd = self.radars[0]  # simples: 1 radar
        if now_t - last_update_t < upd["update_s"]:
            return None
        # checa alcance
        rng_km = distance_haversine(ac["lat"],ac["lon"],upd["lat"],upd["lon"])
        if rng_km > upd["max_range_km"]:
            return {"detect": False, "reason":"out_of_range"}
        # detecção
        detect = (random.random() < upd["pd"])
        # atraso
        dms = self._prop_delay_ms(upd["lat"],upd["lon"],self.controller["lat"],self.controller["lon"])
        jitter = random.uniform(-upd["jitter_ms"], upd["jitter_ms"])
        delay_ms = max(0.0, upd["proc_ms"] + dms + self.ch.get("radar_meas_latency_ms_extra",0) + jitter)
        return {"detect": detect, "delay_ms": delay_ms, "radar_id": upd["id"]}
