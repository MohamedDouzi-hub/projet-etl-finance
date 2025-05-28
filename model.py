import pandas as pd
import statsmodels.api as sm
import numpy as np

class Model:
    def __init__(self, config, repo):
        self.config = config
        self.repo = repo
        self.results = None
        self.sheets_pivots = dict()

    # Jointure des jeux de données
    # Cette méthode effectue deux jointures successives :
    # - Une jointure temporelle entre les données boursières et les données macroéconomiques (€STR) via la date
    # - Une jointure structurelle entre les résultats précédents et les données sectorielles via le ticker
    # Les dates sont préalablement converties pour éviter les problèmes de format.
    # Le résultat final est stocké dans `self.results`, qui servira de base aux analyses et visualisations.
    def join(self) -> None:
        self.repo.stock_data["Date"] = pd.to_datetime(self.repo.stock_data["Date"]).dt.date
        self.repo.macro_data["Date"] = pd.to_datetime(self.repo.macro_data["Date"]).dt.date

        self.results = pd.merge(self.repo.stock_data, self.repo.macro_data, on="Date", how="left")
        self.results = pd.merge(self.results, self.repo.companies_data, on="Ticker", how="left")

    # Calcul des indicateurs financiers
    # Cette méthode enrichit le DataFrame `results` avec trois nouvelles variables clés :
    # - `Return` : rendement journalier des actions, calculé par variation en pourcentage du cours ajusté
    # - `Delta_ESTR` : variation quotidienne du taux €STR
    # - `Volatility` : volatilité mobile (rolling standard deviation) des rendements sur une fenêtre de 20 jours
    # Le tri préalable par entreprise et date permet d'assurer la cohérence des calculs dans les groupes.
    def compute(self) -> None:
        self.results = self.results.sort_values(by=["Ticker", "Date"])
        self.results["Return"] = self.results.groupby("Ticker")["Adj Close"].pct_change()
        self.results["Delta_ESTR"] = self.results["Value"].diff()
        self.results["Volatility"] = self.results.groupby("Ticker")["Return"].rolling(window=20).std().reset_index(0, drop=True)

        # Nettoyage des données finales
        # Suppression des doublons éventuels
        # Remplacement des valeurs manquantes
        # `Return` et `Delta_ESTR` par 0 (pas de variation mesurable)
        # Volatility` par propagation de la dernière valeur connue (forward fill)
        # Réinitialisation de l’index pour assurer une numérotation propre des lignes
        self.results.drop_duplicates(inplace=True)
        self.results["Return"] = self.results["Return"].fillna(0)
        self.results["Delta_ESTR"] = self.results["Delta_ESTR"].fillna(0)
        self.results["Volatility"] = self.results["Volatility"].ffill()
        self.results.reset_index(drop=True, inplace=True)

        # Corrélation simple entre Rendement journaliser et la variation du taux €STR
        df_corr = self.results[["Return", "Delta_ESTR"]].dropna()
        correlation = df_corr["Return"].corr(df_corr["Delta_ESTR"])
        print(f"Corrélation entre Return et Delta_ESTR : {correlation:.4f}")

        # Estime une régression linéaire des rendements en fonction de Delta_ESTR, du taux ESTR et des secteurs.
        # Retourne un DataFrame résumant les coefficients, p-values, t-statistiques et le R².
        df_reg = self.results[["Return", "Delta_ESTR", "Value", "Sector"]].dropna()
        df_reg = pd.get_dummies(df_reg, columns=["Sector"], drop_first=True)

        y = df_reg["Return"].astype(float)
        X = df_reg.drop(columns=["Return"]).astype(float)
        X = sm.add_constant(X)

        model = sm.OLS(y, X).fit()

        summary_df = pd.DataFrame({
            "Coefficient": model.params,
            "P-value": model.pvalues,
            "T-stat": model.tvalues
        })

        r_squared = pd.DataFrame({
            "Coefficient": [model.rsquared],
            "P-value": [np.nan],  # 👈 CORRECTION ici
            "T-stat": [np.nan]
        }, index=["R-squared"])

        summary_df = pd.concat([summary_df, r_squared], axis=0)

        # Ajout de commentaires pour les p-values significatives
        significant_vars = summary_df[pd.to_numeric(summary_df["P-value"], errors="coerce") < 0.05]
        comments = []
        for var in significant_vars.index:
            if var != "R-squared":
                comments.append(f"La variable '{var}' est significative au seuil de 5% (p-value = {summary_df.loc[var, 'P-value']:.4f}).")

        comment_df = pd.DataFrame(comments, columns=[" "])
        empty_row = pd.DataFrame([""] * 2, columns=[" "])
        regression_sheet = pd.concat([
            summary_df.reset_index().rename(columns={"index": " "}),
            empty_row,
            comment_df
        ], ignore_index=True)

        self.sheets_pivots["regression"] = regression_sheet

    def process_pivots(self) -> None:
        """
        Génère des tableaux croisés (pivots) selon les paramètres du fichier de configuration.
        Les résultats sont stockés dans self.sheets_pivots.
        """
        view_data = zip(
            self.config["pivots"]["sheet_names"],
            self.config["pivots"]["view_index"],
            self.config["pivots"]["view_values"],
            self.config["pivots"]["view_columns"],
            self.config["pivots"]["view_aggfunc"],
        )

        for sh, index, values, columns, aggfunc in view_data:
            if sh == "mean_by_sector":
                self.sheets_pivots[sh] = (
                    self.results
                    .groupby("Sector")[["Return", "Volatility"]]
                    .mean()
                    .sort_values(by="Return")
                )
            elif not index:
                print(f"⚠️ Pivot sheet '{sh}' ignoré car aucun index spécifié.")
                continue
            elif columns:
                self.sheets_pivots[sh] = pd.pivot_table(
                    data=self.results,
                    values=values,
                    index=index,
                    columns=columns,
                    aggfunc=aggfunc,
                )
            else:
                self.sheets_pivots[sh] = pd.pivot_table(
                    data=self.results,
                    values=values,
                    index=index,
                    aggfunc=aggfunc,
                )
