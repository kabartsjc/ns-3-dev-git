import datetime
import navdata
import rpl_retriever

def scenario_generator(output_path: str, noise: str):
    scenario_content = []

    # Initialize scenario start time
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    timestamp = start_time.strftime("%H:%M:%S.00")

    # Add basic config lines
    scenario_content += init_config(timestamp, noise)
    waypoints_line, all_navdata =  add_waypoints(timestamp=timestamp)
    scenario_content +=waypoints_line

    scenario_content +=add_routes(timestamp=timestamp)



    

    # Save file
    save_file(output_path, scenario_content)

def init_config(timestamp, noise):
    return [
        f"{timestamp}> CALL brscen/sectors.scn",
        f"{timestamp}> noise {noise}",
        f"{timestamp}> ASAS ON"
    ]


def add_waypoints(timestamp):
    waypoints_line = []
    all_navdata = navdata.load_all_navdata("/home/kabart/github/atc-sim/trial/fix.csv")

    for entry in all_navdata:
        line = f"{timestamp}>DEFWPT {entry.waypoint}, {entry.latitude}, {entry.longitude},FIX"
        waypoints_line.append(line)
    
    return waypoints_line, all_navdata

def add_routes(timestamp):
    route_lines=[]
    rpl_file = "/home/kabart/github/atc-sim/trial/rpl_test.txt"
    rpl_data= rpl_retriever.load_rpl_data(rpl_file=rpl_file)
    for index, rpl_entry in rpl_data.iterrows():
        #0:00:00.00> CRE KLM117 C208/L -23.45 -46.46 270 100 220
        callsign = rpl_entry['callsign']
        aircraft = rpl_entry['aircraft_type']
        origin = rpl_entry['origin']

        line_w = f"{timestamp}>CRE {callsign} {aircraft} {origin} 270 100 200"
        route_lines.append(line_w)

        route = rpl_entry['route']
        parsed_routes=rpl_retriever.parse_route_string(route)

        speed = 0
        altitude = 0
        latitude=0.0
        longitude=0.0

        for line in parsed_routes:
            
            if line['type'] == 'speed_altitude':
                token = line['value']
                f_index = token.index('F')

                speed = int(token[1:f_index])              # 'N0155F090' -> 155
                #CRE SPEED <callsign> <nova_velocidade_em_knots>
                line_w = f"{timestamp}>SPD {callsign} {speed}"
                route_lines.append(line_w)
                
                altitude = int(token[f_index+1:]) * 100    # 'F090' -> 9000
                #CRE ALT <callsign> <nova_altitude_em_pes>
                line_w = f"{timestamp}> ALT {callsign} {altitude}"
                route_lines.append(line_w)
            
            if line['type'] == 'coordinate':
                token = line['value']
                f_index = token.index(',')
                latitude = float(token[1:f_index])   
                longitude = float(token[f_index+1:]) 

                line_w = f"{timestamp}> {callsign} ADDWPT {latitude} {longitude}"
                route_lines.append(line_w)
            
            if line['type'] == 'fix':
                waypoint = line['value']
                #0:00:00.00> KLM117 ADDWPT ZANOR
                line_w = f"{timestamp}> {callsign} ADDWPT {waypoint}"
                route_lines.append(line_w)

        dest = rpl_entry['destination']
        #0:00:00.00> DEST KLM117 SBBR
        line_w = f"{timestamp}> DEST {callsign} {dest}"
        route_lines.append(line_w)
    
    return route_lines




def save_file(file_path, scenario_content):
    with open(file_path, "w") as f:
        f.write("\n".join(scenario_content))
    print(f"✅ Scenario saved to {file_path}")



# Run
file_path = "/home/kabart/bluesky/scenario/my/brt_scen2.scn"
scenario_generator(file_path, "OFF")
