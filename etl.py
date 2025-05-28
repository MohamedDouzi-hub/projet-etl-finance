import os
import pandas as pd
import yaml
from helpers_export import dataframes_to_excel, dataframes_to_db


def enforce_dtypes(df, dtypes: dict) -> pd.DataFrame:
# Fonction utilitaire pour le typage des colonnes
# Cette fonction applique un type explicite à chaque colonne d’un DataFrame
# en se basant sur un dictionnaire {nom_colonne: type_attendu}.
# Elle permet d’assurer la cohérence des types (float, int, datetime, str)
# avant d’enregistrer les données (par ex. dans une base SQLite ou un fichier Excel).
 # Les valeurs non conformes sont converties automatiquement ou remplacées par NaN (avec errors="coerce").

    for col, dtype in dtypes.items():
        if col not in df.columns:
            continue
        if dtype.startswith("datetime"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif dtype.startswith("float"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif dtype.startswith("int"):
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif dtype.startswith("str"):
            df[col] = df[col].astype(str)
    return df


class Etl:
    def __init__(self, config: dict, input_dir: str, excel_path: str, sqlite_path: str):
        self.config = config
        self.input_dir = input_dir
        self.excel_path = excel_path
        self.sqlite_path = sqlite_path

        self.df_stock_raw = pd.DataFrame()
        self.df_stock = pd.DataFrame()
        self.df_macro_raw = pd.DataFrame()
        self.df_macro = pd.DataFrame()
        self.df_companies_raw = pd.DataFrame()
        self.df_companies = pd.DataFrame()

    def extract(self):
        """
        Extrait les fichiers CSV (stock, macro, companies) depuis le répertoire input.
        """
        stock_path = os.path.join(self.input_dir, self.config["files"]["stock_source_file"])
        self.df_stock_raw = pd.read_csv(stock_path, sep=";")

        macro_path = os.path.join(self.input_dir, self.config["files"]["macro_source_file"])
        self.df_macro_raw = pd.read_csv(macro_path, sep=";")

        companies_path = os.path.join(self.input_dir, self.config["files"]["static_companies_file"])
        self.df_companies_raw = pd.read_csv(companies_path, sep=";")

    def transform(self):
        """
        Transforme les données brutes : copie les données financières,
        nettoie et reformate les données macroéconomiques (estr).
        """
        self.df_stock = self.df_stock_raw.copy(deep=True)
        self.df_companies = self.df_companies_raw.copy(deep=True)

        #   → renommage des colonnes
        #   → conversion de la date au format sans heure
        #   → ajout d'une colonne "Indicator" avec la valeur "estr"
        # L’objectif est d’harmoniser les noms de colonnes et les types pour faciliter les jointures et l’analyse.
        df_macro = self.df_macro_raw.copy()
        df_macro = df_macro.rename(columns={"TIME_PERIOD": "Date", "OBS_VALUE": "Value"})
        df_macro["Date"] = pd.to_datetime(df_macro["Date"]).dt.date  # ← ici on retire l'heure
        df_macro["Indicator"] = "estr"
        self.df_macro = df_macro[["Date", "Indicator", "Value"]]

    def load(self):
        """
        Exporte les données transformées vers un fichier Excel et une base SQLite,
        selon les paramètres spécifiés dans la configuration.
        """
        export = {
            self.config["files"]["stock_sheet_name"]: self.df_stock,
            self.config["files"]["macro_sheet_name"]: self.df_macro,
            "companies": self.df_companies
        }

        if self.config["etl_main_parameters"]["to_excel"]:
            dataframes_to_excel(export, self.excel_path)
            print(f"Export Excel : {self.excel_path}")

        if self.config["etl_main_parameters"]["to_sqlite"]:
            dataframes_to_db(
                export,
                db_path=self.sqlite_path,
                drop_all_tables=self.config["etl_main_parameters"]["drop_all_tables"],
            )
            print(f"Export SQLite : {self.sqlite_path}")

    def sanity_check(self):
        """
        Vérifie la cohérence des données transformées :
        - Affiche les dimensions des DataFrames
        - Vérifie la présence des colonnes obligatoires (définies dans config.yaml)
        - Exporte un rapport des types de colonnes dans un fichier Excel
        """
        print("**** Sanity check ****")
        print(f"df_stock.shape = {self.df_stock.shape}")
        print(f"df_macro.shape = {self.df_macro.shape}")
        print(f"df_companies.shape = {self.df_companies.shape}")

        # Vérification des types de colonnes
        report = {
            self.config["files"]["stock_sheet_name"]: self.df_stock.dtypes,
            self.config["files"]["macro_sheet_name"]: self.df_macro.dtypes,
            self.config["files"]["static_companies_sheet_name"]: self.df_companies.dtypes,
        }

        report_path = os.path.join(self.input_dir, self.config["files"]["report_file"])
        dataframes_to_excel(report, report_path)
        print(f"Rapport de types exporté : {report_path}")

        # Vérification des colonnes obligatoires
        for section in ["stock", "macro"]:
            expected_cols = set(self.config["mandatory_columns"][section])
            actual_cols = set(getattr(self, f"df_{section}").columns)
            missing = expected_cols.difference(actual_cols)
            if missing:
                print(f"Colonnes manquantes dans {section} : {missing}")

        print("**** Done ****")

