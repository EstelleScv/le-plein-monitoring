"""
Dashboard Streamlit - Monitoring Le Plein V2
Connexion à la vue agrégée analytics.main.le_plein_monitoring_aggregated
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

# Custom CSS
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
</style>
""", unsafe_allow_html=True)

# Titre
st.markdown('<div class="main-header">⚡ Monitoring Bornes - Le Plein</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Dashboard de monitoring des bornes de recharge</div>', unsafe_allow_html=True)

# Sidebar : Configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Token MotherDuck
    motherduck_token = st.text_input(
        "Token MotherDuck",
        type="password",
        help="Colle ton token MotherDuck ici"
    )
    
    # Sélection du mois
    st.header("📅 Filtres")
    selected_month = st.selectbox(
        "Mois",
        ["2026-05", "2026-04", "2026-03", "2026-02", "2026-01"],
        index=1  # 2026-04 par défaut
    )
    
    # Filtre enseigne
    selected_retailer = st.selectbox(
        "Enseigne",
        ["Toutes"]
    )
    
    refresh = st.button("🔄 Actualiser les données", use_container_width=True)

# Connexion à MotherDuck
@st.cache_resource
def get_motherduck_connection(token):
    """Crée une connexion à MotherDuck"""
    if not token:
        return None
    try:
        connection_string = f'md:analytics?motherduck_token={token}'
        return duckdb.connect(connection_string)
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

# Récupération des données
@st.cache_data(ttl=300)
def fetch_monitoring_data(_con, month):
    """Récupère les données depuis la vue agrégée"""
    if _con is None:
        return None
    
    # Extraire année et mois
    year, month_num = month.split('-')
    
    query = f"""
    SELECT
        retailer AS enseigne,
        store AS site,
        SUM(sessions_lp) AS sessions_lp,
        SUM(clients_lp) AS clients_lp,
        SUM(sessions_fid) AS sessions_fid,
        SUM(sessions_emsp) AS sessions_emsp,
        SUM(sessions_chargemap) AS sessions_chargemap,
        SUM(sessions_totalenergies) AS sessions_totalenergies,
        SUM(sessions_lp + sessions_emsp + sessions_chargemap + sessions_totalenergies) AS sessions_total,
        ROUND(SUM(sessions_lp)::DOUBLE / NULLIF(SUM(sessions_lp + sessions_emsp + sessions_chargemap + sessions_totalenergies), 0) * 100, 1) AS pdm_lp,
        ROUND(SUM(sessions_fid)::DOUBLE / NULLIF(SUM(sessions_lp), 0) * 100, 1) AS taux_fid
    FROM analytics.main.le_plein_monitoring_aggregated
    WHERE YEAR(day) = {year}
      AND MONTH(day) = {month_num}
    GROUP BY retailer, store
    ORDER BY retailer, store
    """
    
    try:
        df = _con.execute(query).fetchdf()
        return df
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        st.code(query)  # Affiche la requête pour debug
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

# Connexion
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
    total_sessions_lp = df['sessions_lp'].sum()
    st.metric(
        label="Sessions Le Plein",
        value=f"{total_sessions_lp:,.0f}",
        help="Nombre total de sessions Le Plein"
    )

with col2:
    avg_pdm = df['pdm_lp'].mean()
    st.metric(
        label="Part de Marché Moyenne",
        value=f"{avg_pdm:.1f}%",
        help="Part de marché moyenne Le Plein"
    )

with col3:
    total_clients = df['clients_lp'].sum()
    st.metric(
        label="Clients Uniques",
        value=f"{total_clients:,.0f}",
        help="Nombre de clients uniques Le Plein"
    )

with col4:
    avg_taux_fid = df['taux_fid'].mean()
    st.metric(
        label="Taux Fidélité Moyen",
        value=f"{avg_taux_fid:.1f}%",
        help="Taux de fidélisation moyen"
    )

# Section : Graphiques
st.header("📈 Analyses")

col1, col2 = st.columns(2)

with col1:
    # Graphique : Sessions par enseigne
    sessions_by_retailer = df.groupby('enseigne')['sessions_lp'].sum().reset_index()
    fig1 = px.bar(
        sessions_by_retailer,
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
    pdm_by_retailer = df.groupby('enseigne')['pdm_lp'].mean().reset_index()
    fig2 = px.bar(
        pdm_by_retailer,
        x='enseigne',
        y='pdm_lp',
        title="Part de Marché Moyenne par Enseigne",
        labels={'pdm_lp': 'PDM (%)', 'enseigne': 'Enseigne'},
        color='pdm_lp',
        color_continuous_scale='Blues'
    )
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# Section : Comparaison opérateurs
st.header("🏢 Comparaison Opérateurs")

total_sessions_by_operator = {
    'Le Plein': df['sessions_lp'].sum(),
    'EMSP': df['sessions_emsp'].sum(),
    'Chargemap': df['sessions_chargemap'].sum(),
    'TotalEnergies': df['sessions_totalenergies'].sum()
}

operator_df = pd.DataFrame(
    list(total_sessions_by_operator.items()),
    columns=['Opérateur', 'Sessions']
)

fig3 = px.pie(
    operator_df,
    values='Sessions',
    names='Opérateur',
    title="Répartition des sessions par opérateur",
    color_discrete_sequence=['#2c5f2d', '#1c4587', '#6a1b9a', '#00838f']
)
st.plotly_chart(fig3, use_container_width=True)

# Section : Tableau détaillé
st.header("📋 Données Détaillées par Site")

# Colonnes à afficher
display_columns = [
    'site', 'enseigne', 'sessions_lp', 'pdm_lp', 'clients_lp',
    'taux_fid', 'sessions_total'
]

# Formater les nombres
df_display = df[display_columns].copy()
df_display['sessions_lp'] = df_display['sessions_lp'].apply(lambda x: f"{x:,.0f}")
df_display['pdm_lp'] = df_display['pdm_lp'].apply(lambda x: f"{x:.1f}%")
df_display['clients_lp'] = df_display['clients_lp'].apply(lambda x: f"{x:,.0f}")
df_display['taux_fid'] = df_display['taux_fid'].apply(lambda x: f"{x:.1f}%")
df_display['sessions_total'] = df_display['sessions_total'].apply(lambda x: f"{x:,.0f}")

# Renommer les colonnes
df_display.columns = [
    'Site', 'Enseigne', 'Sessions LP', 'PDM LP', 'Clients',
    'Taux FID', 'Sessions Total'
]

# Afficher le tableau
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
st.caption(f"Source : analytics.main.le_plein_monitoring_aggregated | Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
