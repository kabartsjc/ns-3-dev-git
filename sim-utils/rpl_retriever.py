import re
import pandas as pd
import datetime

def dms_to_decimal(coord):
    """Convert DMS string like 1631S04229W to decimal degrees (lat, lon)"""
    match = re.match(r"(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])", coord)
    if not match:
        return coord
    lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = match.groups()
    lat = int(lat_deg) + int(lat_min) / 60.0
    lon = int(lon_deg) + int(lon_min) / 60.0
    if lat_dir == 'S':
        lat = -lat
    if lon_dir == 'W':
        lon = -lon
    return f"{lat:.5f},{lon:.5f}"

class RPLFlight:
    def __init__(self, raw_block: str):
        self.raw_block = raw_block
        self.parse_block()

    def parse_block(self):
        lines = self.raw_block.strip().splitlines()
        if not lines or not lines[0].startswith("#C"):
            raise ValueError("Invalid RPL block")
        self.header = lines[0].strip()
        self.route_line = lines[1].strip() if len(lines) > 1 else ""
        self.extra_line = lines[2].strip() if len(lines) > 2 else ""
        self.parse_header()
        self.parse_route()
        self.parse_extra()

    def parse_header(self):
        parts = self.header.split()
        self.start_date = parts[1]
        self.callsign = parts[2]
        self.operating_days = parts[3]
        self.valid_from = parts[4]
        self.valid_to = parts[5]
        self.flight_rules = parts[6]
        self.aircraft_type = parts[7]
        self.rvsm = parts[8]
        self.origin = parts[9]
        self.departure_time = parts[10]

    def parse_route(self):
        segments = self.route_line.split("/")
        processed = []
        for seg in segments:
            seg = seg.strip()
            matches = re.findall(r"\d{4}[NS]\d{5}[EW]", seg)
            for m in matches:
                decimal = dms_to_decimal(m)
                seg = seg.replace(m, decimal)
            processed.append(seg)
        self.route_segments = processed

    def parse_extra(self):
        parts = self.extra_line.split()
        self.destination = parts[0] if len(parts) > 0 else ""
        self.flight_time = parts[1] if len(parts) > 1 else ""
        self.operator = next((p for p in parts if p.startswith("OPR/")), "")
        self.remark = next((p for p in parts if p.startswith("RMK/")), "")
        self.equipment = next((p for p in parts if p.startswith("EQPT/")), "")
        self.pbn = next((p for p in parts if p.startswith("PBN/")), "")
        self.alt = next((p for p in parts if p.startswith("RALT/")), "")
        self.eet = next((p for p in parts if p.startswith("EET/")), "")
        self.performance = next((p for p in parts if p.startswith("PER/")), "")

    def to_dict(self):
        return {
            "callsign": self.callsign,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "days": self.operating_days,
            "origin": self.origin,
            "departure_time": self.departure_time,
            "destination": self.destination,
            "flight_time": self.flight_time,
            "flight_rules": self.flight_rules,
            "aircraft_type": self.aircraft_type,
            "rvsm": self.rvsm,
            "equipment": self.equipment,
            "pbn": self.pbn,
            "route": " | ".join(self.route_segments),
            "alt": self.alt,
            "eet": self.eet,
            "performance": self.performance,
            "operator": self.operator,
            "remark": self.remark,
        }

def parse_rpl_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = re.findall(r"#C .*?@", content, flags=re.DOTALL)
    flights = []
    for block in blocks:
        try:
            flight = RPLFlight(block)
            flights.append(flight.to_dict())
        except Exception:
            continue
    return pd.DataFrame(flights)

def load_fix_dictionary(csv_path):
    import pandas as pd
    fix_df = pd.read_csv(csv_path)
    fix_dict = {
        row['fix_name']: {'latitude': row['latitude'], 'longitude': row['longitude']}
        for _, row in fix_df.iterrows()
    }
    return fix_dict




def classify_and_split_token(token):
    """
    Classify a route token and split speed/altitude tokens into separate fields.
    Returns a dictionary with keys: value, type, speed, altitude.
    """
    if re.match(r"^N\d{4}F\d{3}$", token):  # Speed/Altitude format
        speed = int(token[1:5])  # extract speed part
        altitude = int(token[6:]) * 100  # extract altitude part, in feet
        return {"value": token, "type": "speed_altitude", "speed": speed, "altitude": altitude}
    elif re.match(r"^-?\d+\.\d+,-?\d+\.\d+$", token):
        return {"value": token, "type": "coordinate", "speed": None, "altitude": None}
    elif token in {"DCT", "VFR", "IFR"}:
        return {"value": token, "type": "nav_instruction", "speed": None, "altitude": None}
    else:
        return {"value": token, "type": "fix", "speed": None, "altitude": None}

def parse_route_string(route_str):
    """Parse a route string into a list of (value, type, speed, altitude) entries."""
    entries = []
    tokens = [t.strip() for t in str(route_str).split('|') if t.strip()]
    for token in tokens:
        for sub in token.split():
            entries.append(classify_and_split_token(sub))
    return entries

def load_rpl_data(rpl_file):

    input_file =rpl_file
    rpl_data = parse_rpl_file(input_file)
    
    return rpl_data


# Exemplo 1: Com coordenadas
route_example_1 = " | N0155F090 DCT -16.51667,-42.48333 | N0155F075 VFR DCT"
parsed_route_1 = parse_route_string(route_example_1)
print("--- Rota Exemplo 1 ---")
for i, segment in enumerate(parsed_route_1):
    print(f"Segmento {i+1}: {segment}")
print("\n")

# Exemplo 2: Com fixes (waypoints nomeados)
route_example_2 = " | N0155F080 DCT GENBI DCT MEVUT | N0155F090 DCT LOKAR DCT -20.71667,-48.56667 | N0155F075 VFR DCT"
parsed_route_2 = parse_route_string(route_example_2)
print("--- Rota Exemplo 2 ---")
for i, segment in enumerate(parsed_route_2):
    print(f"Segmento {i+1}: {segment}")
print("\n")

# Exemplo 3: Rota mais simples (apenas um segmento)
route_example_3 = " | N0450F350 GEPMO UZ24 MAVGU"
parsed_route_3 = parse_route_string(route_example_3)
print("--- Rota Exemplo 3 ---")
for i, segment in enumerate(parsed_route_3):
    print(f"Segmento {i+1}: {segment}")
print("\n")


#output_csv="/home/kabart/github/atc-sim/trial/rpl.csv"
#df_updated.to_csv(output_csv, index=False)
