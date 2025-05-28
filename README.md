
# 📊 Analyse de l'impact du taux €STR sur la performance des entreprises du CAC 40

Projet réalisé dans le cadre du cours **Applied Data Science in Finance**  
**Master 1 MBFA – Université Paris 1 Panthéon-Sorbonne**  
Année universitaire : 2024-2025  
Encadrant : Fabrice Galan

## 🎯 Objectif du projet

L'objectif de ce projet est d'évaluer l'impact du taux €STR et de ses variations (`Delta_ESTR`) sur les rendements et la volatilité de 8 entreprises cotées au CAC 40, en contrôlant les effets sectoriels, afin d’analyser la transmission d’éventuels chocs monétaires (variation du taux €STR `Delta_ESTR`) sur le marché boursier.  
Le projet suit une approche modulaire avec des étapes d'extraction, transformation et chargement (ETL), modélisation statistique et restitution via une interface Streamlit.

---

## 📁 Structure du projet

```
├── config.yaml                # Fichier de configuration
├── etl_download.py            # Téléchargement des données via API
├── etl.py                     # Pipeline ETL (extract / transform / load)
├── helpers_export.py          # Fonctions d’export Excel / SQLite
├── helpers_serialize.py       # Chargement fichiers .yaml/.json/.toml
├── model.py                   # Modèles de traitement (régression, stats)
├── repository.py              # Chargement des données depuis la base
├── view.py                    # Visualisation des résultats + dashboard
├── main.py                    # Lancement principal + Streamlit intégré
├── run_streamlit.py           # Point d'entrée rapide via streamlit
└── input/ / output/           # Données brutes / résultats
```

---

## 🔄 Données utilisées

- **Données de marché** : via l’API `yfinance` pour 8 entreprises CAC 40 (MC.PA, TTE.PA, BNP.PA, etc.)
- **Taux €STR** : fichiers CSV BCE
- **Fichier sectoriel** : mapping Ticker → Secteur

---

## ⚙️ Fonctionnalités

✅ Extraction et nettoyage des données financières et macroéconomiques  
✅ Intégration d’un **pipeline ETL modulaire**  
✅ Export vers Excel (.xlsx) avec **coloration conditionnelle**  
✅ Enregistrement dans une base de données SQLite  
✅ Régressions linéaires multiples et statistiques sectorielles  
✅ Interface **Streamlit** interactive :  
   - Filtres par secteur et dates  
   - Graphiques de rendement / volatilité  
   - **Heatmap des corrélations**  
   - Visualisation des statistiques par secteur  

---

## 📊 Résultats produits

- Fichiers `.xlsx` dans `output/` avec feuilles :
  - `summary_statistics`
  - `regression`
  - `mean_by_sector`
- Fichiers `.png` :
  - `histogram_sector_stats.png`
  - `return_TICKER.png`
  - `volatility_time_series.png`
- Base SQLite : `output/output_v01.db`

---

## ▶️ Lancement du projet

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancer l'application
```bash
python run_streamlit.py
```

### 3. Configuration (`config.yaml`)
Détermine les chemins d’entrée/sortie, version, fichiers, paramètres ETL, etc.

---

## 📚 Ressources utilisées

- [yfinance](https://pypi.org/project/yfinance/)
- [Streamlit](https://streamlit.io/)
- [Seaborn](https://seaborn.pydata.org/)
- [SQLite](https://www.sqlite.org/index.html)
- Cours DataCamp :
  - *Exploratory Data Analysis*
  - *Reshaping Data with Pandas*
  - *Introduction to SQL in Python*

---

## 👨‍💻 Auteurs

Projet réalisé par Mohamed Douzi, Ayman Oubaaqa et Khrystyna Kateryna Valenia
(GROUPE A)

