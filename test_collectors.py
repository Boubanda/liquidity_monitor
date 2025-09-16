import unittest
import pandas as pd
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.api_collectors import LiquidityDataCollector

class TestLiquidityDataCollector(unittest.TestCase):
    """Tests pour le collecteur de données"""
    
    def setUp(self):
        """Setup avant chaque test"""
        self.collector = LiquidityDataCollector(data_path="./test_data")
    
    def test_collect_market_data(self):
        """Test de collecte des données de marché"""
        df = self.collector.collect_market_data()
        
        # Vérifier que le DataFrame n'est pas vide
        self.assertFalse(df.empty, "Les données de marché ne devraient pas être vides")
        
        # Vérifier les colonnes requises
        required_columns = ['date', 'instrument', 'close', 'source']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Colonne manquante: {col}")
    
    def test_collect_ecb_rates(self):
        """Test de collecte des taux BCE"""
        df = self.collector.collect_ecb_rates()
        
        if not df.empty:  # API peut être indisponible
            required_columns = ['date', 'rate_type', 'value', 'source']
            for col in required_columns:
                self.assertIn(col, df.columns, f"Colonne manquante: {col}")

if __name__ == '__main__':
    unittest.main()