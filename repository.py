import pandas as pd
from sqlalchemy import create_engine

class Repository:
    def __init__(self, config, db_path: str):
        """
        Initialise le repository avec la configuration et le chemin de la base de données.
        """
        self.config = config
        self.db_path = db_path
        self.stock_data = None
        self.macro_data = None
        self.companies_data = None

    def get_data(self):
        """
        Récupère les données stockées dans la base SQLite (stock, macro, entreprises).
        """
        engine = create_engine(f"sqlite:///{self.db_path}")

        self.stock_data = pd.read_sql(f"SELECT * FROM {self.config['files']['stock_sheet_name']}", engine)
        self.macro_data = pd.read_sql(f"SELECT * FROM {self.config['files']['macro_sheet_name']}", engine)
        self.companies_data = pd.read_sql(f"SELECT * FROM {self.config['files']['static_companies_sheet_name']}", engine)

        print(f"stock_data.shape = {self.stock_data.shape}")
        print(f"macro_data.shape = {self.macro_data.shape}")
