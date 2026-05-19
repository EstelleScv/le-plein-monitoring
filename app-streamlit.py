"""
Dashboard Streamlit - Monitoring Le Plein
Connexion directe à MotherDuck + Interface moderne
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Monitoring Le Plein",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS pour un design moderne
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #231f20;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6a6a6a;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Titre
st.markdown('<div class="main-header">⚡ Monitoring Bornes - Le Plein</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Dashboard de monitoring des bornes de recharge</div>', unsafe_allow_html=True)

# Sidebar : Configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Token MotherDuck (stocké de manière sécurisée)
    motherduck_token = st.text_input(
        "Token MotherDuck",
        type="password",
        help="Colle ton token MotherDuck ici. Il sera stocké uniquement dans ta session."
    )
    
    # Sélection du mois
    st.header("📅 Filtres")
    selected_month = st.selectbox(
        "Mois",
        ["2026-05", "2026-04", "2026-03", "2026-02", "2026-01"],
        index=3  # 2026-02 par défaut
    )
    
    # Filtre enseigne (sera rempli dynamiquement)
    selected_enseigne = st.selectbox(
        "Enseigne",
        ["Toutes"]
    )
    
    # Bouton de rafraîchissement
    refresh = st.button("🔄 Actualiser les données", use_container_width=True)

# Fonction de connexion à MotherDuck
@st.cache_resource
def get_motherduck_connection(token):
    """Crée une connexion à MotherDuck"""
    if not token:
        return None
    try:
        connection_string = f'md:production-data?motherduck_token={token}'
        return duckdb.connect(connection_string)
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

# Fonction pour récupérer les données
@st.cache_data(ttl=300)  # Cache pendant 5 minutes
def fetch_monitoring_data(_con, month):
    """Récupère les données de monitoring depuis MotherDuck"""
    if _con is None:
        return None
    
    query = f"""
    WITH monthly_sessions AS (
      SELECT
        lps.store AS site,
        lps.retailer AS enseigne,
        strftime(DATE_TRUNC('month', lps.started_at), '%Y-%m') AS mois,
        COUNT(DISTINCT lps.id) AS sessions_all,
        COUNT(DISTINCT CASE WHEN lps.token_type = 'APP_USER' THEN lps.id END) AS sessions_lp,
        SUM(lps.energy_kwh) AS kwh_livre,
        SUM(CASE WHEN lps.token_type = 'APP_USER' THEN lps.energy_kwh ELSE 0 END) AS kwh_lp,
        COUNT(DISTINCT CASE WHEN lps.token_type = 'RFID' THEN lps.id END) AS sessions_rfid,
        COUNT(DISTINCT CASE WHEN ll.status IN ('ok', 'N/A', 'bypass') THEN ll.le_plein_session_id END) AS sessions_fid,
        COUNT(DISTINCT CASE WHEN lps.token_type = 'APP_USER' THEN lps.user_id END) AS clients_uniques,
        AVG(lps.plugged_in_duration_in_min) AS temps_branch_moy,
        COUNT(DISTINCT CASE WHEN cp.max_power_in_kw <= 22 THEN lps.id END) AS sessions_eco,
        COUNT(DISTINCT CASE WHEN cp.max_power_in_kw > 22 AND cp.max_power_in_kw <= 100 THEN lps.id END) AS sessions_fast,
        COUNT(DISTINCT CASE WHEN cp.max_power_in_kw > 100 THEN lps.id END) AS sessions_ultra
      FROM "production-data"."silver"."le_plein_billable_sessions" lps
      LEFT JOIN "production-data"."silver"."loyalty_ledger" ll ON lps.id = ll.le_plein_session_id
      LEFT JOIN "production-data"."silver"."charging_points" cp ON lps.evse_id = cp.evse_id
      WHERE strftime(DATE_TRUNC('month', lps.started_at), '%Y-%m') = '{month}'
      GROUP BY 1, 2, 3
    ),
    availability AS (
      SELECT
        s.internal_name AS site,
        COUNT(DISTINCT cp.evse_id) AS pdc_actifs,
        COUNT(DISTINCT CASE WHEN cp.status != 'available' THEN cp.evse_id END) AS pdc_hs
      FROM "production-data"."silver"."charging_points" cp
      JOIN "production-data"."silver"."stations" s ON cp.station_id = s.id
      WHERE s.in_le_plein_network = TRUE
      GROUP BY 1
    )
    SELECT
      ms.*,
      COALESCE(a.pdc_actifs, 0) AS pdc_actifs,
      COALESCE(a.pdc_hs, 0) AS pdc_hs,
      ROUND(ms.sessions_lp::DOUBLE / NULLIF(ms.sessions_all, 0) * 100, 1) AS pdm_lp,
      ROUND(ms.sessions_rfid::DOUBLE / NULLIF(ms.sessions_all, 0) * 100, 1) AS pdm_rfid,
      ROUND(ms.sessions_fid::DOUBLE / NULLIF(ms.sessions_lp, 0) * 100, 1) AS taux_fid,
      ROUND(ms.sessions_eco::DOUBLE / NULLIF(ms.sessions_all, 0) * 100, 1) AS pct_eco,
      ROUND(ms.sessions_fast::DOUBLE / NULLIF(ms.sessions_all, 0) * 100, 1) AS pct_fast,
      ROUND(ms.sessions_ultra::DOUBLE / NULLIF(ms.sessions_all, 0) * 100, 1) AS pct_ultra
    FROM monthly_sessions ms
    LEFT JOIN availability a ON ms.site = a.site
    ORDER BY ms.enseigne, ms.site
    """
    
    try:
        df = _con.execute(query).fetchdf()
        return df
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return None

# Vérification du token
if not motherduck_token:
    st.warning("⚠️ Colle ton token MotherDuck dans la barre latérale pour commencer")
    st.info("""
    **Comment obtenir ton token :**
    1. Va sur https://app.motherduck.com
    2. Clique sur ton profil → Settings → Access Tokens
    3. Crée un nouveau token (Read/Write)
    4. Copie-le et colle-le dans la barre latérale
    """)
    st.stop()

# Connexion à MotherDuck
con = get_motherduck_connection(motherduck_token)

if con is None:
    st.error("❌ Impossible de se connecter à MotherDuck. Vérifie ton token.")
    st.stop()

# Récupération des données
with st.spinner("Chargement des données..."):
    df = fetch_monitoring_data(con, selected_month)

if df is None or df.empty:
    st.warning("Aucune donnée disponible pour ce mois.")
    st.stop()

# Section : KPI Cards
st.header("📊 Indicateurs Clés")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sessions = df['sessions_lp'].sum()
    st.metric(
        label="Sessions Le Plein",
        value=f"{total_sessions:,.0f}",
        delta=None,
        help="Nombre total de sessions Le Plein"
    )

with col2:
    avg_pdm = df['pdm_lp'].mean()
    st.metric(
        label="Part de Marché Moyenne",
        value=f"{avg_pdm:.1f}%",
        delta=None,
        help="Part de marché moyenne Le Plein"
    )

with col3:
    total_clients = df['clients_uniques'].sum()
    st.metric(
        label="Clients Uniques",
        value=f"{total_clients:,.0f}",
        delta=None,
        help="Nombre de clients uniques"
    )

with col4:
    total_energy = df['kwh_lp'].sum() / 1000
    st.metric(
        label="Énergie Livrée",
        value=f"{total_energy:.1f}k kWh",
        delta=None,
        help="Énergie totale livrée"
    )

# Section : Graphiques
st.header("📈 Analyses")

col1, col2 = st.columns(2)

with col1:
    # Graphique : Sessions par enseigne
    sessions_by_enseigne = df.groupby('enseigne')['sessions_lp'].sum().reset_index()
    fig1 = px.bar(
        sessions_by_enseigne,
        x='enseigne',
        y='sessions_lp',
        title="Sessions Le Plein par Enseigne",
        labels={'sessions_lp': 'Sessions', 'enseigne': 'Enseigne'},
        color='sessions_lp',
        color_continuous_scale='Greens'
    )
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Graphique : Part de marché par enseigne
    pdm_by_enseigne = df.groupby('enseigne')['pdm_lp'].mean().reset_index()
    fig2 = px.bar(
        pdm_by_enseigne,
        x='enseigne',
        y='pdm_lp',
        title="Part de Marché Moyenne par Enseigne",
        labels={'pdm_lp': 'PDM (%)', 'enseigne': 'Enseigne'},
        color='pdm_lp',
        color_continuous_scale='Blues'
    )
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# Section : Mix de puissance
st.header("⚡ Mix de Puissance")

col1, col2, col3 = st.columns(3)

with col1:
    avg_eco = df['pct_eco'].mean()
    st.metric("% Eco (≤22kW)", f"{avg_eco:.1f}%")

with col2:
    avg_fast = df['pct_fast'].mean()
    st.metric("% Fast (22-100kW)", f"{avg_fast:.1f}%")

with col3:
    avg_ultra = df['pct_ultra'].mean()
    st.metric("% Ultra (>100kW)", f"{avg_ultra:.1f}%")

# Graphique camembert
power_mix = pd.DataFrame({
    'Type': ['Eco', 'Fast', 'Ultra'],
    'Percentage': [avg_eco, avg_fast, avg_ultra]
})

fig3 = px.pie(
    power_mix,
    values='Percentage',
    names='Type',
    title="Répartition du Mix de Puissance",
    color_discrete_sequence=['#00838f', '#1c4587', '#6a1b9a']
)
st.plotly_chart(fig3, use_container_width=True)

# Section : Tableau détaillé
st.header("📋 Données Détaillées par Site")

# Colonnes à afficher
display_columns = [
    'site', 'enseigne', 'sessions_lp', 'pdm_lp', 'clients_uniques',
    'kwh_lp', 'taux_fid', 'pdc_actifs', 'pdc_hs'
]

# Formater les nombres
df_display = df[display_columns].copy()
df_display['sessions_lp'] = df_display['sessions_lp'].apply(lambda x: f"{x:,.0f}")
df_display['pdm_lp'] = df_display['pdm_lp'].apply(lambda x: f"{x:.1f}%")
df_display['clients_uniques'] = df_display['clients_uniques'].apply(lambda x: f"{x:,.0f}")
df_display['kwh_lp'] = df_display['kwh_lp'].apply(lambda x: f"{x:,.0f}")
df_display['taux_fid'] = df_display['taux_fid'].apply(lambda x: f"{x:.1f}%")

# Renommer les colonnes
df_display.columns = [
    'Site', 'Enseigne', 'Sessions LP', 'PDM LP', 'Clients',
    'kWh LP', 'Taux FID', 'PDC Actifs', 'PDC HS'
]

# Afficher le tableau avec possibilité de tri
st.dataframe(
    df_display,
    use_container_width=True,
    height=400
)

# Export
st.download_button(
    label="📥 Télécharger les données (CSV)",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name=f'monitoring_le_plein_{selected_month}.csv',
    mime='text/csv'
)

# Footer
st.markdown("---")
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")