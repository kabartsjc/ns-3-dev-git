import pandas as pd
from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class NavData:
    #airport: str
    waypoint: str
    #type: str
    latitude: float
    longitude: float
    #altitude_ft: Optional[int]  # in feet

def dms_to_decimal(dms_str: str) -> float:
    """Convert DMS string like 22°14'01"S to decimal degrees"""
    match = re.match(r"(\d+)°(\d+)'(\d+)[\"′]([NSWE])", dms_str.replace("’", "'"))
    if not match:
        return 0.0  # fallback
    degrees, minutes, seconds, direction = match.groups()
    decimal = int(degrees) + int(minutes) / 60 + int(seconds) / 3600
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def parse_altitude(alt_str: str) -> Optional[int]:
    """Convert FL or feet string to integer feet"""
    if pd.isna(alt_str):
        return None
    if str(alt_str).upper().startswith("FL"):
        return int(alt_str[2:]) * 100
    try:
        return int(alt_str)
    except ValueError:
        return None

def load_all_navdata(csv_file: str) -> List[NavData]:
    """Load all navdata entries from the CSV file"""
    df = pd.read_csv(csv_file)
    return [
        NavData(
            #airport=row['AIRPORT'],
            waypoint=row['FIX_NAME'],
            #type=row['TYPE'].upper(),
            latitude=(row['LATITUDE']),
            longitude=(row['LONGITUDE'])
            #altitude_ft=parse_altitude(row['ALTITUDE'])
        )
        for _, row in df.iterrows()
    ]


def filter_by_waypoint(navdata_list: List[NavData], waypoint_name: str) -> List[NavData]:
    return [entry for entry in navdata_list if entry.waypoint == waypoint_name]


