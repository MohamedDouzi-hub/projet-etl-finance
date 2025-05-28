import os
import streamlit as st

from etl import Etl
from model import Model
from repository import Repository
from view import View
from helpers_serialize import get_serialized_data  # à ajouter si pas présent

CONFIG_FILE = "config.yaml"


def _get_config_path() -> str:
    """
    Retourne le chemin absolu vers le fichier de configuration.
    """
    return os.path.join(os.getcwd(), CONFIG_FILE)


def _get_paths(config: dict) -> tuple[str, str, str, str]:
    """
    Génère les chemins complets vers les fichiers d'entrée et de sortie à partir de la configuration.
    """
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, config["file_parameters"]["input_dir"])
    output_dir = os.path.join(base_dir, config["file_parameters"]["output_dir"])
    os.makedirs(output_dir, exist_ok=True)

    version = config["file_parameters"]["version"]

    full_path_output_excel = os.path.join(
        output_dir, config["file_parameters"]["output_file_excel"].format(version)
    )
    full_path_output_sqlite = os.path.join(
        output_dir, config["file_parameters"]["output_file_sqlite"].format(version)
    )
    full_path_output_excel_final = os.path.join(
        output_dir, config["file_parameters"]["output_file_excel_final"].format(version)
    )

    return input_dir, full_path_output_excel, full_path_output_sqlite, full_path_output_excel_final


def run_etl(config: dict, input_dir: str, excel_path: str, sqlite_path: str):
    """
    Exécute les étapes du pipeline ETL : extract, transform, load, sanity check.
    """
    etl = Etl(config, input_dir, excel_path, sqlite_path)
    etl.extract()
    etl.transform()
    etl.load()
    etl.sanity_check()


class App:
    """
    Classe principale qui coordonne le chargement, le traitement et l'affichage des données.
    """
    def __init__(self, config: dict, db_path: str, output_final: str):
        self.config = config
        self.db_path = db_path
        self.output_final = output_final
        self.repo = None
        self.model = None
        self.view = None

    def run(self):
        """
        Lance l'exécution du programme : chargement, traitement et export des résultats.
        """
        self.repo = Repository(self.config, self.db_path)
        self.repo.get_data()

        self.model = Model(self.config, self.repo)
        self.model.join()
        self.model.compute()
        self.model.process_pivots()

        self.view = View(self.config, self.repo, self.model, self.output_final)
        self.view.export()


# Interface Streamlit
if __name__ == "__main__":
    config = get_serialized_data(_get_config_path())
    input_dir, excel_path, db_path, final_excel = _get_paths(config)

    if config["run_mode"]["run_etl"]:
        run_etl(config, input_dir, excel_path, db_path)

    if config["run_mode"]["run_program"]:
        app = App(config, db_path, final_excel)
        app.run()

        st.title("Analyse des performances d'entreprises CAC 40")

        tickers = app.model.results["Ticker"].unique()
        selected_ticker = st.selectbox("Choisir une entreprise", tickers)

        df_filtered = app.model.results[app.model.results["Ticker"] == selected_ticker]
        st.subheader(f"Données pour {selected_ticker}")
        st.dataframe(df_filtered[["Date", "Return", "Volatility", "Delta_ESTR"]].reset_index(drop=True))

        st.line_chart(df_filtered.set_index("Date")["Return"], use_container_width=True)
        st.line_chart(df_filtered.set_index("Date")["Volatility"], use_container_width=True)

        if "mean_by_sector" in app.model.sheets_pivots:
            st.subheader("Statistiques par secteur")
            st.dataframe(app.model.sheets_pivots["mean_by_sector"])

        st.subheader("Graphiques enregistrés")
        for name in [
            "histogram_sector_stats.png",
            f"return_{selected_ticker.replace('.', '_')}.png",
            "volatility_time_series.png"
        ]:
            path = os.path.join(config["file_parameters"]["output_dir"], name)
            if os.path.exists(path):
                st.image(path, caption=name)

                # Dashboard interactif
        app.view.display_interactive_dashboard()