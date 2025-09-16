import yfinance as yf
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from typing import Dict, Optional, List
import time
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiquidityDataCollector:
    """
    Collecteur de données de liquidité pour le monitoring qualité
    Sources: BCE, Yahoo Finance, Alpha Vantage
    """
    
    def __init__(self, data_path: str = "./data/raw"):
        self.data_path = data_path
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Crée les dossiers de données si nécessaire"""
        directories = [
            self.data_path,
            f"{self.data_path}/ecb",
            f"{self.data_path}/market",
            f"{self.data_path}/quality_logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def collect_ecb_rates(self) -> pd.DataFrame:
        """Collecte les taux de la BCE (EURIBOR)"""
        try:
            url = "https://sdw-wsrest.ecb.europa.eu/service/data/FM/D.U2.EUR.RT.MM.EURIBOR1MD_.HSTA"
            headers = {'Accept': 'application/vnd.sdmx.data+json;version=1.0.0'}
            
            logger.info("🔄 Collecte des taux BCE...")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraction des données SDMX
                observations = data['data']['dataSets'][0]['observations']
                dates = data['data']['structure']['dimensions']['observation'][0]['values']
                
                records = []
                for obs_key, obs_data in observations.items():
                    date_idx = int(obs_key.split(':')[0])
                    date_str = dates[date_idx]['id']
                    value = obs_data[0] if obs_data[0] is not None else None
                    
                    records.append({
                        'date': pd.to_datetime(date_str),
                        'rate_type': 'EURIBOR_1M',
                        'value': value,
                        'source': 'ECB',
                        'collection_time': datetime.now()
                    })
                
                df = pd.DataFrame(records)
                
                # Sauvegarde
                filename = f"ecb_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.data_path, "ecb", filename)
                df.to_csv(filepath, index=False)
                
                logger.info(f"✅ BCE: {len(df)} enregistrements collectés")
                return df
                
            else:
                logger.error(f"❌ Erreur BCE API: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Erreur collection BCE: {str(e)}")
            return pd.DataFrame()
    
    def collect_market_data(self) -> pd.DataFrame:
        """Collecte données de marché via Yahoo Finance"""
        try:
            tickers = {
                '^TNX': 'US_10Y_Treasury',
                '^IRX': 'US_3M_Treasury', 
                '^FVX': 'US_5Y_Treasury',
                'EURUSD=X': 'EUR_USD_Rate',
                'BTC-USD': 'Bitcoin_USD'
            }
            
            all_data = []
            logger.info("🔄 Collecte des données de marché...")
            
            for ticker, name in tickers.items():
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="30d")
                    
                    if not hist.empty:
                        for date, row in hist.iterrows():
                            all_data.append({
                                'date': date.date(),
                                'instrument': name,
                                'ticker': ticker,
                                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                                'high': float(row['High']) if pd.notna(row['High']) else None,
                                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                                'close': float(row['Close']) if pd.notna(row['Close']) else None,
                                'volume': int(row['Volume']) if 'Volume' in row and pd.notna(row['Volume']) else None,
                                'source': 'Yahoo_Finance',
                                'collection_time': datetime.now()
                            })
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur pour {ticker}: {str(e)}")
                    continue
            
            df = pd.DataFrame(all_data)
            
            if not df.empty:
                filename = f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.data_path, "market", filename)
                df.to_csv(filepath, index=False)
                
                logger.info(f"✅ Market: {len(df)} enregistrements collectés")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur collection Market: {str(e)}")
            return pd.DataFrame()
    
    def collect_alpha_vantage_data(self, api_key: Optional[str] = None) -> pd.DataFrame:
        """Collecte via Alpha Vantage (optionnel)"""
        if not api_key:
            logger.info("ℹ️ Alpha Vantage ignoré (pas de clé API)")
            return pd.DataFrame()
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'FEDERAL_FUNDS_RATE',
                'interval': 'monthly',
                'apikey': api_key
            }
            
            logger.info("🔄 Collecte Alpha Vantage...")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    records = []
                    for item in data['data'][:50]:
                        records.append({
                            'date': pd.to_datetime(item['date']),
                            'rate_type': 'FED_FUNDS_RATE',
                            'value': float(item['value']),
                            'source': 'Alpha_Vantage',
                            'collection_time': datetime.now()
                        })
                    
                    df = pd.DataFrame(records)
                    
                    filename = f"alpha_vantage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    filepath = os.path.join(self.data_path, "market", filename)
                    df.to_csv(filepath, index=False)
                    
                    logger.info(f"✅ Alpha Vantage: {len(df)} enregistrements collectés")
                    return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ Erreur Alpha Vantage: {str(e)}")
            return pd.DataFrame()
    
    def get_latest_files(self) -> Dict[str, str]:
        """Récupère les fichiers les plus récents de chaque source"""
        latest_files = {}
        
        for source_dir in ['ecb', 'market']:
            source_path = os.path.join(self.data_path, source_dir)
            if os.path.exists(source_path):
                files = [f for f in os.listdir(source_path) if f.endswith('.csv')]
                if files:
                    latest_file = max(files)
                    latest_files[source_dir] = os.path.join(source_path, latest_file)
        
        return latest_files
    
    def run_full_collection(self, alpha_vantage_key: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Lance la collecte complète de toutes les sources"""
        logger.info("🚀 Début de la collecte de données...")
        start_time = datetime.now()
        
        results = {
            'ecb_data': self.collect_ecb_rates(),
            'market_data': self.collect_market_data(),
            'alpha_vantage_data': self.collect_alpha_vantage_data(alpha_vantage_key)
        }
        
        # Log de synthèse
        total_records = sum(len(df) for df in results.values())
        duration = datetime.now() - start_time
        
        log_entry = {
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'total_records': total_records,
            'sources_status': {
                name: len(df) > 0 for name, df in results.items()
            },
            'individual_counts': {
                name: len(df) for name, df in results.items()
            }
        }
        
        # Sauvegarde du log
        log_file = os.path.join(self.data_path, "quality_logs", 
                               f"collection_log_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        logger.info(f"✅ Collection terminée: {total_records} enregistrements en {duration.total_seconds():.1f}s")
        
        return results