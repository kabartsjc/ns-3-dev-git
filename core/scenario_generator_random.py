import datetime
import navdata
from navdata import NavData

import airports
from airports import Airport

import geoutils.geo as geo

import core.aircrafts as aicrafts
from core.aircrafts import Aircraft

from typing import List, Optional
import random

import math


def scenario_generator(output_path: str, noise: str, num_aircraft:int, max_num_routes=int):
    scenario_content = []

    # Initialize scenario start time
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    timestamp = start_time.strftime("%H:%M:%S.00")

    
    # Add basic config lines
    scenario_content += init_config(timestamp, noise)

    waypoints_line, all_navdata = add_waypoints(timestamp=timestamp)
    scenario_content +=waypoints_line

    aircrafts_lines = generate_aircraft(timestamp,all_navdata,num_aircraft,max_num_routes)
    scenario_content +=aircrafts_lines






     

    # Save file
    save_file(output_path, scenario_content)

def add_waypoints(timestamp):
    waypoints_line = []
    all_navdata = navdata.load_all_navdata("/home/kabart/github/atc-sim/config/fix.csv")

    for entry in all_navdata:
        line = f"{timestamp}>DEFWPT {entry.waypoint}, {entry.latitude}, {entry.longitude},FIX"
        waypoints_line.append(line)
    
    return waypoints_line, all_navdata


def init_config(timestamp, noise):
    return [
        f"{timestamp}> CALL brscen/sectors.scn",
        f"{timestamp}> noise {noise}",
        f"{timestamp}> ASAS ON",
        f"#########",
        f"#########"
    ]

def generate_aircraft(orig_timestamp,navdata=List[NavData],num_air=int, max_number_routes=int ):
    aircraft_lines=[]
    airport_db = airports.load_airports("/home/kabart/github/atc-sim/config/simuairports.csv")
    aircrafts_db = aicrafts.load_aicrafts("/home/kabart/github/atc-sim/config/bada_common_aircrafts.csv")

    for i in range(num_air):
        #generate create aircraft
        #0:00:00.00> CRE KLM117 C208/L -23.45 -46.46 270 100 220

        #check if the timestamp will be updated
        timestamp = orig_timestamp
        random_i = random.randint(0, 1)
       # if random_i==0:
        #    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
         #   # Gera um valor aleatório entre 0 e 7200 segundos
          #  random_offset = random.randint(0, 7200)
           ## # Soma ao timestamp inicial
            #new_time =start_time + datetime.timedelta(seconds=random_offset)
            #timestamp = new_time.strftime("%H:%M:%S.00")


        line_w=f"#########"
        aircraft_lines.append(line_w)

        line_w=f"#########"
        aircraft_lines.append(line_w)
       
        callsign = f"ABC{i}"

        aircraft_idx = random.randint(0, len(aircrafts_db) - 1)

        aircraft = aircrafts_db[aircraft_idx]

        aircraft_code = aircraft.icao_code
        spd = aircraft.speed
        
        origin_idx = random.randint(0, len(airport_db) - 1)

        origin = airport_db[origin_idx]

        origin_code = origin.airport_icao
        elevation = random.randint(1000, 5000)
        if elevation <0:
            elevation*-1
        heading = origin.runway_heading

        if math.isnan(heading):
            heading = 0.0

        line_w = f"{timestamp}>CRE {callsign} {aircraft_code} {origin_code} {heading} {elevation} {spd}"
        aircraft_lines.append(line_w)


        #0:00:00.00> DEST KLM117 SBBR
        dest_idx = random.randint(0, len(airport_db) - 1)
        while dest_idx==origin_idx:
            dest_idx = random.randint(0, len(airport_db) - 1)

        dest = airport_db[dest_idx]

        dest_code = dest.airport_icao
        
        dest_lat = dest.latitude
        dest_long = dest.longitude

        route = geo.generate_random_route_between_airports(origin, dest,navdata,max_number_routes) 
        for wp in route:
            #0:00:00.00> KLM117 ADDWPT ALBOK
            wp.waypoint
            
            line_w = f"{timestamp}> {callsign} ADDWPT {wp.waypoint}"
            aircraft_lines.append(line_w)



        line_w = f"{timestamp}> DEST {callsign} {dest_lat} {dest_long}"
        aircraft_lines.append(line_w)


        # Example usage inside your generator:
        speed_knots =aircraft.speed
        route_latlon = [(origin.latitude,origin.longitude), (dest.latitude, dest.longitude)]  # origin -> dest (or via waypoints)
        ete = geo.ete_seconds_km(route_latlon, speed_knots)
        buffer = 300  # +5 min safety

        start_off = ts_to_seconds(timestamp)
        rmv_abs = start_off + ete + buffer

        rmv_time = seconds_to_ts(rmv_abs)

        line_w = f"{timestamp}> DEST {callsign} {dest_code}"
        #line_w = f"{rmv_time}> DELRTE {callsign}"
        aircraft_lines.append(line_w)

        aircraft_lines.append(f"#########")
        aircraft_lines.append(f"#########")
    return aircraft_lines




def ts_to_seconds(ts: str) -> int:
    # "HH:MM:SS.00" -> segundos
    h, m, s = ts.split(":")
    s = s.split(".")[0]
    return int(h)*3600 + int(m)*60 + int(s)

def seconds_to_ts(sec: int) -> str:
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}.00"

    
def save_file(file_path, scenario_content):
    with open(file_path, "w") as f:
        f.write("\n".join(scenario_content))
    print(f"✅ Scenario saved to {file_path}")




# Run
file_path = "/home/kabart/bluesky/scenario/my/brt_scen8.scn"
scenario_generator(file_path, noise="ON",num_aircraft=100, max_num_routes=4)

