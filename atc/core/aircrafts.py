from dataclasses import dataclass
import pandas as pd
from typing import List

@dataclass
class Aircraft:
    icao_code: str
    name: str
    speed: float
    cruise_min: float
    cruise_max: float

def load_aicrafts(csv_file: str) -> List[Aircraft]:
    """Load all aircraft entries from the CSV file"""
    df = pd.read_csv(csv_file)
    return [
        Aircraft(
            icao_code=row['icao_code'],
            name=row['aircraft_name'],
            speed=row['speed'],
            cruise_min=row['cruise_min'],
            cruise_max=row['cruise_max']
        )
        for _, row in df.iterrows()
    ]
