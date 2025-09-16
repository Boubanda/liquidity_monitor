import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data_collection.api_collectors import LiquidityDataCollector
from src.data_quality.quality_checks import DataQualityChecker
from src.data_quality.anomaly_detection import AnomalyDetector

# Configuration de la page
st.set_page_config(
    page_title="🏦 Liquidity Data Quality Monitor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .quality-good { border-left-color: #51cf66 !important; }
    .quality-warning { border-left-color: #ffd43b !important; }
    .quality-bad { border-left-color: #ff6b6b !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache 5 minutes
def load_data():
    """Charge les données avec cache"""
    collector = LiquidityDataCollector()
    
    # Charger les fichiers les plus récents
    latest_files = collector.get_latest_files()
    data = {}
    
    for source, filepath in latest_files.items():
        try:
            df = pd.read_csv(filepath)
            data[source] = df
        except Exception as e:
            st.error(f"Erreur chargement {source}: {str(e)}")
            data[source] = pd.DataFrame()
    
    return data

@st.cache_data(ttl=300)
def load_quality_reports():
    """Charge les rapports de qualité"""
    reports_path = "./data/quality_reports"
    if not os.path.exists(reports_path):
        return []
    
    reports = []
    for filename in os.listdir(reports_path):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(reports_path, filename), 'r') as f:
                    report = json.load(f)
                    reports.append(report)
            except Exception:
                continue
    
    return sorted(reports, key=lambda x: x['timestamp'], reverse=True)

def display_kpi_cards(data):
    """Affiche les KPI principaux"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_records = sum(len(df) for df in data.values())
    active_sources = sum(1 for df in data.values() if not df.empty)
    
    with col1:
        st.metric(
            label="📊 Total Records",
            value=f"{total_records:,}",
            delta=f"{active_sources} sources actives"
        )
    
    # Calcul de la fraîcheur moyenne
    freshness_scores = []
    for source, df in data.items():
        if not df.empty and 'collection_time' in df.columns:
            latest_time = pd.to_datetime(df['collection_time']).max()
            hours_old = (datetime.now() - latest_time).total_seconds() / 3600
            freshness = max(0, 1 - hours_old / 24)  # Score sur 24h
            freshness_scores.append(freshness)
    
    avg_freshness = sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0
    
    with col2:
        st.metric(
            label="⏱️ Data Freshness",
            value=f"{avg_freshness*100:.1f}%",
            delta="Dernière collecte"
        )
    
    with col3:
        # Calcul du taux de complétude
        completeness_scores = []
        for df in data.values():
            if not df.empty:
                completeness = 1 - df.isnull().sum().sum() / (len(df) * len(df.columns))
                completeness_scores.append(completeness)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        st.metric(
            label="✅ Completeness",
            value=f"{avg_completeness*100:.1f}%",
            delta="Données valides"
        )
    
    with col4:
        # Calcul des anomalies
        total_anomalies = 0
        for df in data.values():
            if not df.empty:
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                for col in numeric_cols:
                    if len(df[col].dropna()) > 0:
                        z_scores = abs((df[col] - df[col].mean()) / df[col].std())
                        total_anomalies += (z_scores > 3).sum()
        
        st.metric(
            label="⚠️ Anomalies",
            value=total_anomalies,
            delta="Valeurs aberrantes"
        )

def display_data_overview(data):
    """Affiche la vue d'ensemble des données"""
    st.subheader("📊 Vue d'ensemble des données")
    
    # Graphique temporel
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Taux BCE (EURIBOR)', 'Taux US Treasury', 'EUR/USD', 'Volume des données'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (source, df) in enumerate(data.items()):
        if df.empty:
            continue
        
        color = colors[i % len(colors)]
        
        if source == 'ecb' and 'value' in df.columns:
            df_plot = df.copy()
            df_plot['date'] = pd.to_datetime(df_plot['date'])
            df_plot = df_plot.sort_values('date')
            
            fig.add_trace(
                go.Scatter(
                    x=df_plot['date'],
                    y=df_plot['value'],
                    name='EURIBOR 1M',
                    line=dict(color=color),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
        
        elif source == 'market' and 'close' in df.columns:
            df_plot = df.copy()
            df_plot['date'] = pd.to_datetime(df_plot['date'])
            
            # Treasury rates
            treasury_data = df_plot[df_plot['instrument'].str.contains('Treasury', na=False)]
            if not treasury_data.empty:
                for instrument in treasury_data['instrument'].unique():
                    inst_data = treasury_data[treasury_data['instrument'] == instrument].sort_values('date')
                    fig.add_trace(
                        go.Scatter(
                            x=inst_data['date'],
                            y=inst_data['close'],
                            name=instrument,
                            line=dict(color=color),
                            mode='lines'
                        ),
                        row=1, col=2
                    )
            
            # EUR/USD
            eur_usd_data = df_plot[df_plot['instrument'] == 'EUR_USD_Rate']
            if not eur_usd_data.empty:
                eur_usd_data = eur_usd_data.sort_values('date')
                fig.add_trace(
                    go.Scatter(
                        x=eur_usd_data['date'],
                        y=eur_usd_data['close'],
                        name='EUR/USD',
                        line=dict(color='#2ca02c'),
                        mode='lines'
                    ),
                    row=2, col=1
                )
    
    # Volume par jour
    daily_counts = {}
    for source, df in data.items():
        if not df.empty and 'date' in df.columns:
            daily_count = df.groupby(pd.to_datetime(df['date']).dt.date).size()
            for date, count in daily_count.items():
                daily_counts[date] = daily_counts.get(date, 0) + count
    
    if daily_counts:
        dates = list(daily_counts.keys())
        counts = list(daily_counts.values())
        
        fig.add_trace(
            go.Bar(
                x=dates,
                y=counts,
                name='Records/jour',
                marker_color='#9467bd'
            ),
            row=2, col=2
        )
    
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

def display_quality_dashboard():
    """Affiche le dashboard de qualité"""
    st.subheader("🔍 Dashboard Qualité")
    
    # Charger les données
    data = load_data()
    
    if not any(data.values()):
        st.warning("Aucune donnée disponible. Lancez une collecte d'abord.")
        return
    
    # Générer rapport de qualité en temps réel
    quality_checker = DataQualityChecker()
    quality_report = quality_checker.generate_quality_report(data)
    
    # Score global
    overall_score = quality_report['overall_score']
    score_color = "🟢" if overall_score > 0.8 else "🟡" if overall_score > 0.6 else "🔴"
    
    st.metric(
        label=f"{score_color} Score Qualité Global",
        value=f"{overall_score*100:.1f}%",
        delta=f"Basé sur {len(data)} sources"
    )
    
    # Détails par source
    cols = st.columns(len(data))
    for i, (source, source_report) in enumerate(quality_report['sources'].items()):
        with cols[i]:
            score = source_report['quality_score']
            score_color = "#51cf66" if score > 0.8 else "#ffd43b" if score > 0.6 else "#ff6b6b"
            
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {score_color}">
                <h4>{source.upper()}</h4>
                <p><strong>Score:</strong> {score*100:.1f}%</p>
                <p><strong>Records:</strong> {source_report['record_count']:,}</p>
                <p><strong>Complétude:</strong> {source_report['completeness']['completeness_score']*100:.1f}%</p>
                <p><strong>Fraîcheur:</strong> {source_report['freshness']['freshness_score']*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)

def display_anomaly_detection():
    """Affiche la détection d'anomalies"""
    st.subheader("🚨 Détection d'Anomalies")
    
    data = load_data()
    
    if not any(data.values()):
        st.warning("Aucune donnée disponible.")
        return
    
    detector = AnomalyDetector()
    anomaly_report = detector.generate_anomaly_report(data)
    
    for source, anomalies in anomaly_report['sources'].items():
        st.write(f"### {source.upper()}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Valeurs aberrantes statistiques:**")
            outliers = anomalies['statistical_outliers']
            if outliers:
                for column, stats in outliers.items():
                    if stats['count'] > 0:
                        st.warning(f"{column}: {stats['count']} anomalies ({stats['percentage']:.1f}%)")
            else:
                st.success("Aucune anomalie statistique détectée")
        
        with col2:
            st.write("**Anomalies temporelles:**")
            temporal = anomalies['temporal_anomalies']
            gap_count = len(temporal.get('gaps', []))
            change_count = len(temporal.get('sudden_changes', []))
            
            if gap_count > 0:
                st.warning(f"{gap_count} gaps temporels détectés")
            if change_count > 0:
                st.warning(f"{change_count} variations brutales détectées")
            if gap_count == 0 and change_count == 0:
                st.success("Aucune anomalie temporelle")

def main():
    """Application principale"""
    st.title("🏦 Liquidity Data Quality Monitor")
    st.markdown("**Système de monitoring de la qualité des données de liquidité bancaire**")
    
    # Sidebar pour navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choisir une page",
        ["🏠 Overview", "📊 Data Quality", "🚨 Anomalies", "⚙️ Collection"]
    )
    
    # Bouton de rafraîchissement
    if st.sidebar.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.success("Cache vidé ! Les données seront rechargées.")
    
    # Navigation
    if page == "🏠 Overview":
        data = load_data()
        display_kpi_cards(data)
        st.divider()
        display_data_overview(data)
        
    elif page == "📊 Data Quality":
        display_quality_dashboard()
        
    elif page == "🚨 Anomalies":
        display_anomaly_detection()
        
    elif page == "⚙️ Collection":
        st.subheader("⚙️ Collecte de Données")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Lancer la collecte", type="primary"):
                with st.spinner("Collecte en cours..."):
                    collector = LiquidityDataCollector()
                    results = collector.run_full_collection()
                    
                    st.success("Collecte terminée !")
                    for source, df in results.items():
                        st.write(f"**{source}:** {len(df)} enregistrements")
        
        with col2:
            st.write("**Dernières collectes:**")
            logs_path = "./data/raw/quality_logs"
            if os.path.exists(logs_path):
                log_files = [f for f in os.listdir(logs_path) if f.endswith('.json')]
                for log_file in sorted(log_files, reverse=True)[:5]:
                    st.write(f"📄 {log_file}")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Développé pour Société Générale**")
    st.sidebar.markdown(f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()