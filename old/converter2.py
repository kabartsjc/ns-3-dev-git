#
# A Python script to generate a Bluesky Air Traffic Simulator scenario file (.scn)
# from a list of structured flight data, replicating the structure of a provided
# demo scenario file.
#

import datetime

def generate_bluesky_scenario(flights):
    """
    Generates a Bluesky TrafScript scenario file content with initial setup
    commands and flight data.

    Args:
        flights (list): A list of dictionaries, where each dictionary
                        represents a flight with its details and route.

    Returns:
        str: The complete content of the Bluesky scenario file.
    """
    scenario_content = []

    # --- Initial Setup Commands ---
    # These commands are taken from the user's provided scenario file
    scenario_content.append("0:00:00.00>noise off")
    scenario_content.append("0:00:00.00>ASAS ON")
    
    # We will use the 'pan' command to center the simulation.
    # The first flight's departure airport is used for this purpose.
    if flights:
        pan_command = f"0:00:00.00>pan {flights[0]['departure_icao'].lower()}"
        scenario_content.append(pan_command)
    
    scenario_content.append("0:00:00.00>call Sectors/NL/ALL")
    scenario_content.append("")  # Add a blank line for readability

    # The AREA command is often used to define the simulation boundaries.
    # We'll use a placeholder since the specific coordinates are not in the
    # provided flight data.
    scenario_content.append("# 0:00:00.00>datalog on")
    scenario_content.append("0:00:00.00>AREA,  53.84926725,   2.66901,  50.841097,   10.64189,  46.849073,   10.600248,")
    
    
    # --- Flight Data Commands ---
    
    # Loop through each flight in the provided list.
    # The timestamp is set to the start of the simulation (0:00:00.00)
    # for all aircraft, as seen in the demo file.
    timestamp = "0:00:00.00>"
    for flight in flights:
        
        # 1. Create the aircraft using the CRE command, now including lat/lon.
        # Syntax: CRE <callsign> <aircraft_type> <lat> <lon> <heading> <altitude> <speed>
        cre_command = (
            f"{timestamp} CRE {flight['callsign']} {flight['aircraft_type']} "
            f"{flight['initial_lat']} {flight['initial_lon']} "
            f"{flight['initial_heading']} {flight['initial_altitude']} "
            f"{flight['initial_speed']}"
        )
        scenario_content.append(cre_command)
        
        # 2. Add the destination airport using the DEST command.
        # Syntax: DEST <callsign> <destination_icao>
        dest_command = (
            f"{timestamp} DEST {flight['callsign']} {flight['destination_icao']}"
        )
        scenario_content.append(dest_command)

        # 3. Add RNAV waypoints using the ADDWPT command (optional for this update,
        # but kept for future use if needed). The user's provided file doesn't
        # use ADDWPT, so we won't add it in this specific output, but the
        # function can be extended.

    # Join all the command strings into a single block of text
    return "\n".join(scenario_content)


# --- Sample Data ---
# This is a mock-up of what your flight data might look like.
# It now includes latitude and longitude for the initial position.

flight_data = [
    {
        "callsign": "KLM117",
        "aircraft_type": "B738",
        "departure_icao": "EHAM",
        "destination_icao": "LEMD", # New destination field
        "initial_lat": 52.3086,
        "initial_lon": 4.7639,
        "initial_heading": 270,
        "initial_altitude": "FL250", # Using Flight Level format
        "initial_speed": 220,
    },
    {
        "callsign": "AFR982",
        "aircraft_type": "A320",
        "departure_icao": "LFPG",
        "destination_icao": "LSGG",
        "initial_lat": 49.0097,
        "initial_lon": 2.5479,
        "initial_heading": 220,
        "initial_altitude": "FL300",
        "initial_speed": 240,
    },
    {
        "callsign": "BAW455",
        "aircraft_type": "B772",
        "departure_icao": "EGLL",
        "destination_icao": "EDDF",
        "initial_lat": 51.4700,
        "initial_lon": -0.4543,
        "initial_heading": 120,
        "initial_altitude": "FL400",
        "initial_speed": 250,
    }
]

# --- Main execution block ---
if __name__ == "__main__":
    scenario_file_content = generate_bluesky_scenario(flight_data)
    
    # Print the content to the console
    print("--- Generated Bluesky Scenario (.scn) Content ---")
    print(scenario_file_content)

    # Save the content to a file.
    file_path = "/home/kabart/bluesky/scenario/my/my_new_scenario.scn"
    try:
        with open(file_path, "w") as f:
            f.write(scenario_file_content)
        print(f"\nScenario successfully saved to {file_path}")
    except IOError as e:
        print(f"\nError writing to file {file_path}: {e}")

