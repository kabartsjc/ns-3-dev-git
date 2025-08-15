from dataclasses import dataclass
import pandas as pd
from typing import List


@dataclass
class Airport:
    airport_icao: str
    latitude: float
    longitude: float
    altitude: float
    runway_heading: float


def load_airports(csv_file: str) -> List[Airport]:
    """Load all airport entries from the CSV file"""
    df = pd.read_csv(csv_file)
    return [
        Airport(
            airport_icao=row['icao_id'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            altitude=row['altitude'],
            runway_heading=row['runway_heading']  # Supondo que este seja o nome correto da coluna
        )
        for _, row in df.iterrows()
    ]
