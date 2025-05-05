import pandas as pd

rpi_df = pd.read_csv("data/rpi.csv")

def get_team_name(cell):
    for line in str(cell).split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""

rpi_df["Team"] = rpi_df["Team"].apply(get_team_name)

elo_df = pd.read_csv("data/elo.csv")

elo_df["Team"] = elo_df["Team"].astype(str).str.strip().str.replace('"', '')

merged_df = pd.merge(rpi_df, elo_df, on="Team", how="left")

merged_df = merged_df[merged_df["Team"] != "Team"]

merged_df = merged_df[["Team", "RPI", "ELO"]]
merged_df.columns = ["team", "rpi_ranking", "elo"]

merged_df.to_csv("data/cleaned_data.csv", index=False)

print("Cleaned data saved to data/cleaned_data.csv")
