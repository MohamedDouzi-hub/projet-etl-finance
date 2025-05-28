import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from helpers_export import dataframes_to_excel

class View:
    def __init__(self, config, repo, model, full_path_output_excel_final):
        self.config = config
        self.repo = repo
        self.model = model
        self.full_path_output_excel_final = full_path_output_excel_final

    def export(self) -> None:
        # Résultat principal (jointure + calculs)
        results = {self.config["files"]["final_sheet"]: self.model.results}

        # Tables croisées (pivots)
        print(f"Export columns={list(self.model.sheets_pivots.keys())}")
        sheets = results | self.model.sheets_pivots

        # Génération du graphique s'il y a la feuille mean_by_sector
        if "mean_by_sector" in self.model.sheets_pivots:
            df_mean = self.model.sheets_pivots["mean_by_sector"].reset_index()
            self._export_sector_plot(df_mean)

        # Export final dans Excel
        dataframes_to_excel(sheets, self.full_path_output_excel_final)
        print(f"Export terminé → {self.full_path_output_excel_final}")

        # Graphiques additionnels
        self._plot_return_time_series()
        self._plot_volatility_time_series()

    def _export_sector_plot(self, df_sector):
        """
        Crée un histogramme des rendements et volatilités moyens par secteur
        et l’enregistre en PNG dans le dossier output.
        """
        bar_width = 0.35
        x = range(len(df_sector))

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar([p - bar_width / 2 for p in x], df_sector["Return"], width=bar_width, label="Return")
        ax.bar([p + bar_width / 2 for p in x], df_sector["Volatility"], width=bar_width, label="Volatility")

        ax.set_xticks(list(x))
        ax.set_xticklabels(df_sector["Sector"], rotation=45, ha="right")
        ax.set_ylabel("Values")
        ax.set_title("Average Return and Volatility by Sector")
        ax.legend()

        output_path = os.path.join(self.config["file_parameters"]["output_dir"], "histogram_sector_stats.png")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"Graphique enregistré : {output_path}")

    def _plot_return_time_series(self):
        """
        Génère 4 graphiques PNG pour DG.PA, BNP.PA, SAN.PA, CA.PA montrant l’évolution du Return.
        """
        df = self.model.results.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values(["Ticker", "Date"], inplace=True)

        output_dir = self.config["file_parameters"]["output_dir"]
        os.makedirs(output_dir, exist_ok=True)

        tickers_to_plot = ["DG.PA", "BNP.PA", "SAN.PA", "CA.PA"]

        for ticker in tickers_to_plot:
            df_ticker = df[df["Ticker"] == ticker]
            if df_ticker.empty:
                print(f"Aucune donnée pour {ticker}")
                continue

            plt.figure(figsize=(10, 4))
            plt.plot(df_ticker["Date"], df_ticker["Return"], label=ticker, linewidth=1.2)
            plt.title(f"Évolution du Return – {ticker}")
            plt.xlabel("Date")
            plt.ylabel("Return")
            plt.grid(True)
            plt.tight_layout()
            plt.legend()

            filename = f"return_{ticker.replace('.', '_')}.png"
            path = os.path.join(output_dir, filename)
            plt.savefig(path)
            plt.close()

            print(f"Graphique enregistré : {path}")

    def _plot_volatility_time_series(self):
        """
        Trace l’évolution de la Volatilité par entreprise dans le temps
        """
        df = self.model.results.dropna(subset=["Volatility"]).copy()
        df["Date"] = pd.to_datetime(df["Date"])

        plt.figure(figsize=(12, 6))
        sns.lineplot(data=df, x="Date", y="Volatility", hue="Ticker")
        plt.title("Évolution de la Volatilité par entreprise")
        plt.xlabel("Date")
        plt.ylabel("Volatility")
        plt.legend(title="Ticker", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        path = os.path.join(self.config["file_parameters"]["output_dir"], "volatility_time_series.png")
        plt.savefig(path)
        plt.close()
        print(f"Graphique Volatility enregistré → {path}")

    def display_interactive_dashboard(self):
        """
        Affiche une interface Streamlit avec filtres, graphiques et heatmap
        pour explorer les données par secteur et période.
        """
        df = self.model.results.copy()
        df["Date"] = pd.to_datetime(df["Date"])

        st.sidebar.header("Filtres")

        secteurs = self.repo.companies_data["Sector"].unique()
        selected_sectors = st.sidebar.multiselect("Secteurs", secteurs, default=list(secteurs))

        min_date = df["Date"].min()
        max_date = df["Date"].max()
        date_range = st.sidebar.date_input("Plage de dates", [min_date, max_date], min_value=min_date,
                                           max_value=max_date)

        df_filtered = df[
            (df["Date"] >= pd.to_datetime(date_range[0])) &
            (df["Date"] <= pd.to_datetime(date_range[1]))
            ]
        df_filtered = df_filtered[df_filtered["Sector"].isin(selected_sectors)]

        st.subheader("Dashboard interactif")
        st.dataframe(
            df_filtered[["Date", "Ticker", "Sector", "Return", "Volatility", "Delta_ESTR"]].reset_index(drop=True))

        st.line_chart(df_filtered.set_index("Date")[["Return", "Volatility"]])

        # Heatmap de corrélation
        st.subheader("Corrélations entre variables")
        corr_cols = ["Return", "Volatility", "Delta_ESTR"]
        df_corr = df_filtered[corr_cols].dropna()

        if df_corr.shape[0] >= 2:  # Minimum 2 lignes pour calculer une corrélation
            corr_matrix = df_corr.corr()

            fig, ax = plt.subplots(figsize=(5, 4))
            sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", square=True, ax=ax)
            ax.set_title("Heatmap des corrélations")
            st.pyplot(fig)
        else:
            st.info("Pas assez de données pour afficher la heatmap.")

