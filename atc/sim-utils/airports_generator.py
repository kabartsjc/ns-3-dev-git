import pandas as pd

# Download manual the files:
# - https://davidmegginson.github.io/ourairports-data/airports.csv
# - https://davidmegginson.github.io/ourairports-data/runways.csv

airports_df = pd.read_csv("/home/kabart/github/atc-sim/config/airports.csv")
runways_df = pd.read_csv("/home/kabart/github/atc-sim/config/runways.csv")

# Filter with the desired information (ICAO code started with 'SB')
sb_airports = airports_df[
    (airports_df['ident'].str.startswith('SB')) &
    (airports_df['type'].isin(['small_airport', 'medium_airport', 'large_airport']))
].copy()

# Select and rename the colunms
sb_airports = sb_airports[['ident', 'name', 'iso_country', 'latitude_deg', 'longitude_deg', 'elevation_ft']]
sb_airports = sb_airports.rename(columns={
    'ident': 'icao_id',
    'name': 'nome',
    'iso_country': 'pais',
    'latitude_deg': 'latitude',
    'longitude_deg': 'longitude',
    'elevation_ft': 'altitude'
})

# Calculate the average  heading in the runways
runways_df = runways_df[['airport_ident', 'le_heading_degT', 'he_heading_degT']]
runways_df['runway_heading'] = runways_df[['le_heading_degT', 'he_heading_degT']].mean(axis=1)
avg_heading = runways_df.groupby('airport_ident')['runway_heading'].mean().reset_index()
avg_heading = avg_heading.rename(columns={'airport_ident': 'icao_id'})

# MIx with the airport data
sb_airports = sb_airports.merge(avg_heading, on='icao_id', how='left')

# export to CSV
sb_airports.to_csv("/home/kabart/github/atc-sim/config/simuairports.csv", index=False)

print("CSV generated: aeroportos_brasileiros_SB.csv")
