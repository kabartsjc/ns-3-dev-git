import pandas as pd
import requests
from io import StringIO

# Step 1: Download OurAirports navaids data
url = "https://ourairports.com/data/navaids.csv"
response = requests.get(url)

if response.status_code != 200:
    raise Exception("Failed to download OurAirports data")

navaids_df = pd.read_csv(StringIO(response.text))

# Step 2: Load your fix list (replace this with your own path)
fixes_df = pd.read_csv("named_fixes.csv")  # Your extracted list

# Step 3: Filter OurAirports for Brazilian fixes and join on 'ident'
navaids_brazil = navaids_df[navaids_df['country'] == 'BR']
fixes_with_coords = fixes_df.merge(
    navaids_brazil[['ident', 'latitude_deg', 'longitude_deg']],
    left_on='fix_name',
    right_on='ident',
    how='left'
)

# Step 4: Rename and clean output
fixes_with_coords = fixes_with_coords.drop(columns=['ident'])
fixes_with_coords = fixes_with_coords.rename(columns={
    "latitude_deg": "latitude",
    "longitude_deg": "longitude"
})

# Step 5: Save result
fixes_with_coords.to_csv("named_fixes_with_coords.csv", index=False)
print("✔ named_fixes_with_coords.csv generated successfully.")
