import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class AnomalyDetector:
    """Détecteur d'anomalies pour les données financières"""
    
    def __init__(self, std_threshold: float = 3.0):
        self.std_threshold = std_threshold
    
    def detect_statistical_outliers(self, df: pd.DataFrame, 
                                  numeric_columns: List[str]) -> Dict[str, Any]:
        """Détecte les valeurs aberrantes statistiques (méthode Z-score)"""
        outliers = {}
        
        for column in numeric_columns:
            if column in df.columns and df[column].dtype in ['float64', 'int64']:
                values = df[column].dropna()
                
                if len(values) > 0:
                    try:
                        # Calcul Z-score
                        mean_val = values.mean()
                        std_val = values.std()
                        
                        if std_val > 0:
                            z_scores = np.abs((values - mean_val) / std_val)
                            outlier_indices = np.where(z_scores > self.std_threshold)[0]
                            
                            outliers[column] = {
                                'count': len(outlier_indices),
                                'percentage': len(outlier_indices) / len(values) * 100,
                                'outlier_values': values.iloc[outlier_indices].tolist(),
                                'z_scores': z_scores[outlier_indices].tolist()
                            }
                        else:
                            outliers[column] = {
                                'count': 0,
                                'percentage': 0.0,
                                'outlier_values': [],
                                'z_scores': []
                            }
                    except Exception:
                        outliers[column] = {
                            'count': 0,
                            'percentage': 0.0,
                            'outlier_values': [],
                            'z_scores': []
                        }
        
        return outliers
    
    def detect_temporal_anomalies(self, df: pd.DataFrame, 
                                 date_column: str = 'date',
                                 value_column: str = 'value') -> Dict[str, Any]:
        """Détecte les anomalies temporelles (gaps, variations brutales)"""
        if df.empty or date_column not in df.columns:
            return {'gaps': [], 'sudden_changes': []}
        
        try:
            # Trier par date
            df_sorted = df.sort_values(date_column)
            df_sorted[date_column] = pd.to_datetime(df_sorted[date_column])
            
            # Détection des gaps temporels
            gaps = []
            if len(df_sorted) > 1:
                time_diffs = df_sorted[date_column].diff()
                median_diff = time_diffs.median()
                
                for i, diff in enumerate(time_diffs):
                    if pd.notna(diff) and diff > median_diff * 3:  # Gap > 3x médiane
                        gaps.append({
                            'index': i,
                            'gap_duration': str(diff),
                            'date_before': df_sorted.iloc[i-1][date_column].isoformat(),
                            'date_after': df_sorted.iloc[i][date_column].isoformat()
                        })
            
            # Détection des variations brutales
            sudden_changes = []
            if value_column in df_sorted.columns:
                values = df_sorted[value_column].dropna()
                if len(values) > 1:
                    pct_changes = values.pct_change().abs()
                    threshold = pct_changes.quantile(0.95)  # Top 5% des variations
                    
                    extreme_changes = pct_changes[pct_changes > threshold]
                    for idx, change in extreme_changes.items():
                        sudden_changes.append({
                            'index': int(idx),
                            'percentage_change': float(change * 100),
                            'value_before': float(values.iloc[idx-1]) if idx > 0 else None,
                            'value_after': float(values.iloc[idx])
                        })
            
            return {
                'gaps': gaps,
                'sudden_changes': sudden_changes
            }
            
        except Exception:
            return {'gaps': [], 'sudden_changes': []}
    
    def detect_business_rule_violations(self, df: pd.DataFrame, 
                                       rules: Dict[str, Any]) -> Dict[str, Any]:
        """Détecte les violations de règles métier"""
        violations = {}
        
        for rule_name, rule_config in rules.items():
            try:
                column = rule_config.get('column')
                rule_type = rule_config.get('type')
                
                if column not in df.columns:
                    continue
                
                if rule_type == 'range':
                    min_val = rule_config.get('min')
                    max_val = rule_config.get('max')
                    
                    violations_mask = (
                        (df[column] < min_val) | (df[column] > max_val)
                    ) if min_val is not None and max_val is not None else False
                    
                    violation_count = violations_mask.sum() if hasattr(violations_mask, 'sum') else 0
                    
                    violations[rule_name] = {
                        'type': 'range_violation',
                        'count': int(violation_count),
                        'percentage': float(violation_count / len(df) * 100) if len(df) > 0 else 0
                    }
                
                elif rule_type == 'not_null':
                    null_count = df[column].isnull().sum()
                    violations[rule_name] = {
                        'type': 'null_violation',
                        'count': int(null_count),
                        'percentage': float(null_count / len(df) * 100) if len(df) > 0 else 0
                    }
                    
            except Exception as e:
                violations[rule_name] = {
                    'type': 'error',
                    'error': str(e)
                }
        
        return violations
    
    def generate_anomaly_report(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Génère un rapport d'anomalies complet"""
        timestamp = datetime.now()
        report = {
            'timestamp': timestamp.isoformat(),
            'sources': {}
        }
        
        # Règles métier par défaut
        business_rules = {
            'rate_positive': {
                'column': 'value',
                'type': 'range',
                'min': 0,
                'max': 100
            },
            'price_not_null': {
                'column': 'close',
                'type': 'not_null'
            }
        }
        
        for source_name, df in data_dict.items():
            if df.empty:
                continue
            
            # Colonnes numériques pour détection statistique
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            source_report = {
                'statistical_outliers': self.detect_statistical_outliers(df, numeric_columns),
                'temporal_anomalies': self.detect_temporal_anomalies(df),
                'business_rule_violations': self.detect_business_rule_violations(df, business_rules)
            }
            
            report['sources'][source_name] = source_report
        
        return report