import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path

class DataQualityChecker:
    """Vérificateur de qualité des données de liquidité"""
    
    def __init__(self, quality_report_path: str = "./data/quality_reports"):
        self.quality_report_path = quality_report_path
        Path(quality_report_path).mkdir(parents=True, exist_ok=True)
    
    def check_completeness(self, df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        """Vérifie la complétude des données"""
        if df.empty:
            return {
                'completeness_score': 0.0,
                'missing_columns': required_columns,
                'missing_values_by_column': {},
                'total_missing_percentage': 100.0
            }
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        missing_values = {}
        total_values = len(df) * len(df.columns)
        total_missing = 0
        
        for column in df.columns:
            missing_count = df[column].isnull().sum()
            missing_values[column] = {
                'count': int(missing_count),
                'percentage': float(missing_count / len(df) * 100)
            }
            total_missing += missing_count
        
        completeness_score = 1.0 - (total_missing / total_values)
        
        return {
            'completeness_score': float(completeness_score),
            'missing_columns': missing_columns,
            'missing_values_by_column': missing_values,
            'total_missing_percentage': float(total_missing / total_values * 100)
        }
    
    def check_freshness(self, df: pd.DataFrame, date_column: str = 'date', 
                       max_age_hours: int = 24) -> Dict[str, Any]:
        """Vérifie la fraîcheur des données"""
        if df.empty or date_column not in df.columns:
            return {
                'is_fresh': False,
                'latest_date': None,
                'age_hours': None,
                'freshness_score': 0.0
            }
        
        try:
            df[date_column] = pd.to_datetime(df[date_column])
            latest_date = df[date_column].max()
            current_time = datetime.now()
            
            if pd.isna(latest_date):
                age_hours = float('inf')
            else:
                age_hours = (current_time - latest_date).total_seconds() / 3600
            
            is_fresh = age_hours <= max_age_hours
            freshness_score = max(0.0, 1.0 - (age_hours / (max_age_hours * 2)))
            
            return {
                'is_fresh': bool(is_fresh),
                'latest_date': latest_date.isoformat() if pd.notna(latest_date) else None,
                'age_hours': float(age_hours) if age_hours != float('inf') else None,
                'freshness_score': float(freshness_score)
            }
            
        except Exception:
            return {
                'is_fresh': False,
                'latest_date': None,
                'age_hours': None,
                'freshness_score': 0.0
            }
    
    def check_duplicates(self, df: pd.DataFrame, 
                        subset_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Vérifie les doublons"""
        if df.empty:
            return {
                'duplicate_count': 0,
                'duplicate_percentage': 0.0,
                'has_duplicates': False
            }
        
        duplicate_count = df.duplicated(subset=subset_columns).sum()
        duplicate_percentage = duplicate_count / len(df) * 100
        
        return {
            'duplicate_count': int(duplicate_count),
            'duplicate_percentage': float(duplicate_percentage),
            'has_duplicates': bool(duplicate_count > 0)
        }
    
    def generate_quality_report(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Génère un rapport de qualité complet"""
        timestamp = datetime.now()
        report = {
            'timestamp': timestamp.isoformat(),
            'sources': {},
            'overall_score': 0.0
        }
        
        source_scores = []
        
        for source_name, df in data_dict.items():
            if df.empty:
                source_report = {
                    'record_count': 0,
                    'completeness': self.check_completeness(df, []),
                    'freshness': self.check_freshness(df),
                    'duplicates': self.check_duplicates(df),
                    'quality_score': 0.0
                }
            else:
                # Définir les colonnes requises selon le type de données
                if 'ecb' in source_name.lower():
                    required_columns = ['date', 'rate_type', 'value']
                elif 'market' in source_name.lower():
                    required_columns = ['date', 'instrument', 'close']
                else:
                    required_columns = list(df.columns)
                
                completeness = self.check_completeness(df, required_columns)
                freshness = self.check_freshness(df)
                duplicates = self.check_duplicates(df)
                
                # Calcul du score de qualité
                quality_score = (
                    completeness['completeness_score'] * 0.4 +
                    freshness['freshness_score'] * 0.4 +
                    (1.0 - duplicates['duplicate_percentage'] / 100) * 0.2
                )
                
                source_report = {
                    'record_count': len(df),
                    'completeness': completeness,
                    'freshness': freshness,
                    'duplicates': duplicates,
                    'quality_score': float(quality_score)
                }
            
            report['sources'][source_name] = source_report
            source_scores.append(source_report['quality_score'])
        
        # Score global
        if source_scores:
            report['overall_score'] = float(np.mean(source_scores))
        
        # Sauvegarde du rapport
        report_filename = f"quality_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(self.quality_report_path, report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report