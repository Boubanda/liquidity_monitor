# README.md
# ================================
# 🏦 Liquidity Data Quality Monitor

Système de monitoring de la qualité des données de liquidité bancaire développé pour Société Générale.

## 🎯 Objectifs

- Collecter automatiquement des données de liquidité depuis différentes sources
- Monitorer la qualité des données en temps réel
- Détecter les anomalies et violations de règles métier
- Fournir un dashboard interactif pour le suivi

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Setup
```bash
# Cloner le projet
git clone <your-repo>
cd liquidity_monitor

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement (Windows)
venv\Scripts\activate
# Ou (Linux/Mac)
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## 💡 Utilisation

### Collecte de données
```bash
# Collecte simple
python main.py collect

# Avec clé Alpha Vantage
python main.py collect --alpha-key YOUR_API_KEY
```

### Vérification qualité
```bash
python main.py quality
```

### Détection d'anomalies
```bash
python main.py anomalies
```

### Dashboard interactif
```bash
python run_dashboard.py
```
Puis ouvrir http://localhost:8501

## 📊 Sources de données

- **BCE (Banque Centrale Européenne)** : Taux EURIBOR
- **Yahoo Finance** : Obligations d'État, taux de change
- **Alpha Vantage** : Taux de la Fed (optionnel)

## 🔍 Indicateurs de qualité

- **Complétude** : Pourcentage de données valides
- **Fraîcheur** : Âge des dernières données
- **Doublons** : Détection des enregistrements dupliqués
- **Anomalies** : Valeurs aberrantes statistiques et temporelles

## 📁 Structure du projet

```
liquidity_monitor/
├── src/
│   ├── data_collection/     # Collecteurs de données
│   ├── data_quality/        # Vérification qualité
│   ├── dashboard/           # Interface Streamlit
│   └── utils/               # Utilitaires
├── data/                    # Données collectées
├── tests/                   # Tests unitaires
├── main.py                  # Point d'entrée CLI
├── run_dashboard.py         # Lancement dashboard
└── requirements.txt         # Dépendances
```

## 🎨 Dashboard

Le dashboard Streamlit propose :
- Vue d'ensemble des KPI
- Graphiques temporels des données
- Scores de qualité par source
- Alertes d'anomalies en temps réel

## 🔧 Configuration

Modifier `config.yaml` pour :
- Seuils de qualité
- Sources de données
- Paramètres du dashboard

## 📝 Tests

```bash
python -m pytest tests/
```

## 🚀 Déploiement

Le projet est prêt pour :
- Docker (ajouter Dockerfile)
- Scheduling avec cron/systemd
- Déploiement cloud (AWS, Azure, GCP)

## 👨‍💻 Développé par

**Votre Nom** - Candidat alternance Société Générale

## 📄 Licence

Projet académique - Société Générale