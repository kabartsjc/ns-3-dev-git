#
# A Python script to generate a Bluesky Air Traffic Simulator scenario file (.scn)
# from a list of structured flight data.
#

import datetime

def generate_bluesky_scenario(flights):
    """
    Generates a Bluesky TrafScript scenario file content.

    Args:
        flights (list): A list of dictionaries, where each dictionary
                        represents a flight with its details and route.

    Returns:
        str: The complete content of the Bluesky scenario file.
    """
    scenario_content = []
    
    # Initialize a scenario start time. We'll add a delay for each new flight.
    start_time = datetime.datetime(2025, 1, 1, 10, 0, 0)
    
    # Loop through each flight in the provided list
    for i, flight in enumerate(flights):
        
        # Increment the start time for each aircraft to simulate a staggered departure
        flight_time = start_time + datetime.timedelta(seconds=i * 20)
        timestamp = flight_time.strftime("%H:%M:%S.00>")

        # 1. Create the aircraft using the CRE command
        # Syntax: CRE <callsign> <aircraft_type> <initial_position> <heading> <altitude> <speed>
        cre_command = (
            f"{timestamp} CRE {flight['callsign']} {flight['aircraft_type']} "
            f"{flight['departure_icao']} {flight['initial_heading']} "
            f"{flight['initial_altitude']} {flight['initial_speed']}"
        )
        scenario_content.append(cre_command)
        
        # 2. Add RNAV waypoints using the ADDWPT command
        # Syntax: <callsign> ADDWPT <waypoint_name_or_lat_lon> [alt] [speed]
        # We will add waypoints a few seconds after the aircraft is created.
        waypoint_time = flight_time + datetime.timedelta(seconds=5)
        waypoint_timestamp = waypoint_time.strftime("%H:%M:%S.00>")
        
        for waypoint in flight['waypoints']:
            waypoint_command = (
                f"{waypoint_timestamp} {flight['callsign']} ADDWPT {waypoint}"
            )
            scenario_content.append(waypoint_command)

    # Join all the command strings into a single block of text
    return "\n".join(scenario_content)


# --- Sample Data ---
# This is a mock-up of what your flight data might look like.
# In a real-world application, you would load this from a CSV file, a database,
# or an API.

flight_data = [
    {
        "callsign": "KLM117",
        "aircraft_type": "B738",  # Boeing 737-800
        "departure_icao": "EHAM", # Amsterdam Airport Schiphol
        "initial_heading": 270,   # West
        "initial_altitude": 2500, # feet
        "initial_speed": 220,     # knots
        "waypoints": [
            "L980",   # London Airway
            "UN530",  # France Airway
            "UN490",  # Spain Airway
            "LEMD",   # Madrid Barajas Airport
        ]
    },
    {
        "callsign": "AFR982",
        "aircraft_type": "A320",  # Airbus A320
        "departure_icao": "LFPG", # Paris-Charles de Gaulle Airport
        "initial_heading": 220,   # Southwest
        "initial_altitude": 3000, # feet
        "initial_speed": 240,     # knots
        "waypoints": [
            "TULON",
            "NATOR",
            "MIPLI",
            "LSGG",   # Geneva Airport
        ]
    },
    {
        "callsign": "BAW455",
        "aircraft_type": "B772",  # Boeing 777-200
        "departure_icao": "EGLL", # London Heathrow Airport
        "initial_heading": 120,   # Southeast
        "initial_altitude": 4000, # feet
        "initial_speed": 250,     # knots
        "waypoints": [
            "DVR",
            "WIZ",
            "L612",
            "N748",
            "N377",
            "EDDF",   # Frankfurt Airport
        ]
    }
]

# --- Main execution block ---
if __name__ == "__main__":
    scenario_file_content = generate_bluesky_scenario(flight_data)
    
    # Print the content to the console
    print("--- Generated Bluesky Scenario (.scn) Content ---")
    print(scenario_file_content)

     # Now, save this content to a file.
    file_path = "/home/kabart/bluesky/scenario/my/my_scenario.scn"
    with open(file_path, "w") as f:
        f.write(scenario_file_content)
    print(f"\nScenario saved to {file_path}")
