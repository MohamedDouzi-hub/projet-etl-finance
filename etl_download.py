import os
import pandas as pd
import yfinance as yf
import requests
import yaml
from io import StringIO

# Charger la config
def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

# Paramètres
tickers = ["MC.PA", "TTE.PA", "BNP.PA", "AIR.PA", "SAN.PA", "ORA.PA", "DG.PA", "CA.PA"]
start = config["start_date"]
end = config["end_date"]

# Données actions CAC 40 via yfinance
print("Téléchargement des données boursières...")
df = yf.download(tickers, start=start, end=end, group_by="ticker", auto_adjust=True)

all_data = []
for ticker in tickers:
    if ticker in df.columns.get_level_values(0):
        df_ticker = df[ticker].copy()
        df_ticker["Ticker"] = ticker
        df_ticker = df_ticker.reset_index()[["Date", "Ticker", "Close", "Volume"]]
        df_ticker.rename(columns={"Close": "Adj Close"}, inplace=True)
        all_data.append(df_ticker)

df_stock = pd.concat(all_data, ignore_index=True)
df_stock.to_csv("input/stock_data.csv", index=False, sep=";")
print(" Fichier stock_data.csv généré.")

# Nettoyage du fichier estr brut et création d'un fichier clean
estr_raw_path = "input/estr.csv"
estr_clean_path = "input/estr_clean.csv"

if os.path.exists(estr_raw_path):
    print("🧼 Nettoyage des données macro (estr)...")

    df = pd.read_csv(estr_raw_path, skiprows=1, header=None)
    df = df.iloc[:, [0, 2]]  # Garder la Date et la Valeur

    df.columns = ["Date", "Value"]
    df["Date"] = pd.to_datetime(df["Date"])
    df["Indicator"] = "estr"
    df = df[["Date", "Indicator", "Value"]]

    df.to_csv(estr_clean_path, index=False, sep=";")
    print(f"Fichier {estr_clean_path} généré proprement.")
else:
    print("Le fichier estr.csv est manquant dans le dossier input/")




# création d'un fichier csv avec le nom des entreprises associé à leur secteur

# Définir les données manuellement
data = [
    {"Ticker": "MC.PA", "Sector": "Luxe"},
    {"Ticker": "TTE.PA", "Sector": "Energie"},
    {"Ticker": "BNP.PA", "Sector": "Banque"},
    {"Ticker": "AIR.PA", "Sector": "Aeronautique"},
    {"Ticker": "SAN.PA", "Sector": "Sante"},
    {"Ticker": "ORA.PA", "Sector": "Telecom"},
    {"Ticker": "DG.PA", "Sector": "BTP"},
    {"Ticker": "CA.PA", "Sector": "Distribution"},
]

df = pd.DataFrame(data)
df.to_csv("input/companies.csv", index=False, sep=";")
print("Fichier companies.csv généré dans input/")
