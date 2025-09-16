#!/usr/bin/env python3
"""
Script pour créer automatiquement main.py avec tout son contenu
"""

def create_main_py():
    """Crée le fichier main.py avec le code complet"""
    
    main_content = '''#!/usr/bin/env python3
"""
Point d'entrée principal pour le Liquidity Data Quality Monitor
"""

import argparse
import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from src.data_collection.api_collectors import LiquidityDataCollector
from src.data_quality.quality_checks import DataQualityChecker
from src.data_quality.anomaly_detection import AnomalyDetector

def collect_data(args):
    """Lance la collecte de données"""
    print("🚀 Lancement de la collecte de données...")
    
    collector = LiquidityDataCollector(data_path=args.data_path)
    results = collector.run_full_collection(alpha_vantage_key=args.alpha_key)
    
    print(f"\\n📊 Résumé de la collecte:")
    for source, df in results.items():
        if not df.empty:
            print(f"  • {source}: {len(df)} enregistrements")
        else:
            print(f"  • {source}: Aucune donnée")
    
    return results

def check_quality(args):
    """Lance la vérification de qualité"""
    print("🔍 Vérification de la qualité des données...")
    
    # Charger les données les plus récentes
    collector = LiquidityDataCollector(data_path=args.data_path)
    latest_files = collector.get_latest_files()
    
    data = {}
    for source, filepath in latest_files.items():
        try:
            import pandas as pd
            df = pd.read_csv(filepath)
            data[source] = df
            print(f"✅ Chargé {source}: {len(df)} enregistrements")
        except Exception as e:
            print(f"❌ Erreur chargement {source}: {str(e)}")
            data[source] = pd.DataFrame()
    
    # Générer rapport de qualité
    quality_checker = DataQualityChecker()
    quality_report = quality_checker.generate_quality_report(data)
    
    print(f"\\n📋 Score de qualité global: {quality_report['overall_score']*100:.1f}%")
    
    for source, source_report in quality_report['sources'].items():
        score = source_report['quality_score']
        print(f"  • {source}: {score*100:.1f}%")

def detect_anomalies(args):
    """Lance la détection d'anomalies"""
    print("🚨 Détection d'anomalies...")
    
    # Charger les données
    collector = LiquidityDataCollector(data_path=args.data_path)
    latest_files = collector.get_latest_files()
    
    data = {}
    for source, filepath in latest_files.items():
        try:
            import pandas as pd
            df = pd.read_csv(filepath)
            data[source] = df
        except Exception as e:
            print(f"❌ Erreur chargement {source}: {str(e)}")
            data[source] = pd.DataFrame()
    
    # Détecter anomalies
    detector = AnomalyDetector()
    anomaly_report = detector.generate_anomaly_report(data)
    
    for source, anomalies in anomaly_report['sources'].items():
        print(f"\\n{source.upper()}:")
        
        # Anomalies statistiques
        outliers = anomalies['statistical_outliers']
        total_outliers = sum(stats['count'] for stats in outliers.values())
        if total_outliers > 0:
            print(f"  🔴 {total_outliers} valeurs aberrantes détectées")
        else:
            print(f"  ✅ Aucune anomalie statistique")
        
        # Anomalies temporelles
        temporal = anomalies['temporal_anomalies']
        gaps = len(temporal.get('gaps', []))
        changes = len(temporal.get('sudden_changes', []))
        
        if gaps > 0:
            print(f"  ⚠️ {gaps} gaps temporels")
        if changes > 0:
            print(f"  ⚠️ {changes} variations brutales")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description='Liquidity Data Quality Monitor - Société Générale',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py collect                    # Collecte des données
  python main.py quality                    # Vérification qualité
  python main.py anomalies                  # Détection anomalies
  python main.py collect --alpha-key ABC123 # Avec clé Alpha Vantage
        """
    )
    
    parser.add_argument(
        'command',
        choices=['collect', 'quality', 'anomalies'],
        help='Commande à exécuter'
    )
    
    parser.add_argument(
        '--alpha-key',
        help='Clé API Alpha Vantage (optionnel)'
    )
    
    parser.add_argument(
        '--data-path',
        default='./data/raw',
        help='Chemin de sauvegarde des données (défaut: ./data/raw)'
    )
    
    args = parser.parse_args()
    
    # Créer les répertoires nécessaires
    Path(args.data_path).mkdir(parents=True, exist_ok=True)
    
    try:
        if args.command == 'collect':
            collect_data(args)
        elif args.command == 'quality':
            check_quality(args)
        elif args.command == 'anomalies':
            detect_anomalies(args)
            
    except KeyboardInterrupt:
        print("\\n⚠️ Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(main_content)
        print("✅ Fichier main.py créé avec succès !")
        print(f"📄 Taille: {len(main_content)} caractères")
        
        # Vérification
        with open('main.py', 'r') as f:
            lines = f.readlines()
        print(f"📝 Nombre de lignes: {len(lines)}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")

if __name__ == "__main__":
    create_main_py()