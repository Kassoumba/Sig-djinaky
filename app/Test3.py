import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import leafmap.foliumap as leafmap
import folium
from folium.plugins import MarkerCluster
import requests
from io import BytesIO

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="SIG Djinaky 2026", page_icon="🌍")

# Style CSS pour l'interface
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
    .hero-section {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;
        border-left: 10px solid #ffa000;
    }
    .card-stat {
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: center;
        border-top: 4px solid #1b5e20;
    }
    .legend-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; padding: 5px; background: #fff; border-radius: 5px; border: 1px solid #eee; }
    .legend-tag { width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CHARGEMENT ET NETTOYAGE (233 POINTS) ---
@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTI7qqNBuvYmXBPB5qCS0COBPBf4vtHHymhI4d4P3_ATD8kX-Tqw5Sv3IMbv0M6u1em4l_fQzclGRLp/pub?output=xlsx"
    
    config = {
        "Poste de Santé": {"color": "red", "hex": "#d32f2f", "icon": "medkit"},
        "École / Lycée": {"color": "purple", "hex": "#7b1fa2", "icon": "graduation-cap"},
        "Forage Hydraulique": {"color": "blue", "hex": "#1976d2", "icon": "tint"},
        "Marché Communal": {"color": "orange", "hex": "#fbc02d", "icon": "shopping-cart"},
        "Ferme Agricole": {"color": "green", "hex": "#388e3c", "icon": "leaf"}
    }

    try:
        response = requests.get(url)
        df = pd.read_excel(BytesIO(response.content), engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # Correction virgule -> point pour Lat/Lon
        for col in ['Lat', 'Lon']:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Harmonisation des noms pour la légende
        df['Type'] = df['Type'].astype(str).str.strip().replace({
            'Poste de Sante': 'Poste de Santé',
            'Ecole/Lycee': 'École / Lycée',
            'Marche Communal': 'Marché Communal'
        })
        
        df['Investissement'] = pd.to_numeric(df['Investissement'], errors='coerce').fillna(0)
        df = df.dropna(subset=['Lat', 'Lon', 'Village'])
        return df, config
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return pd.DataFrame(), config

df_full, map_config = load_data()

# --- 3. BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h2 style='color: #1b5e20;'>O_K_G#95</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio("Menu Principal", ["🏠 Dashboard", "🗺️ Carte Interactive", "📦 Données Brutes"])
    
    st.markdown("### 🗺️ RÉGLAGES CARTE")
    map_choice = st.selectbox("Fond de carte", ["Satellite Hybride", "Google Terrain", "OpenStreetMap", "CartoDB Dark"])
    use_cluster = st.checkbox("Regrouper les icônes (Cluster)", value=True)

    st.markdown("### 🛠️ FILTRES")
    f_village = st.selectbox("Filtrer par Village", ["Tous les villages"] + sorted(list(df_full["Village"].unique())))
    f_type = st.selectbox("Filtrer par Type", ["Tous les types"] + list(map_config.keys()))

    st.markdown("---")
    st.markdown("### 📋 PATRIMOINE")
    for k, v in map_config.items():
        count = len(df_full[df_full["Type"] == k])
        st.markdown(f'<div class="legend-row"><div style="display:flex;align-items:center;"><div class="legend-tag" style="background:{v["hex"]};"></div><span style="font-size:11px;">{k}</span></div><b>{count}</b></div>', unsafe_allow_html=True)

# --- 4. FILTRAGE DYNAMIQUE ---
df_view = df_full.copy()
if f_village != "Tous les villages":
    df_view = df_view[df_view["Village"] == f_village]
if f_type != "Tous les types":
    df_view = df_view[df_view["Type"] == f_type]

# --- 5. AFFICHAGE DES PAGES ---

if page == "🏠 Dashboard":
    st.markdown(f"""<div class="hero-section"><h1>📍 SIG Communal - Djinaky 2026</h1><p>Vue : {f_village} | {f_type}</p></div>""", unsafe_allow_html=True)

    # Métriques
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="card-stat"><small>Infrastructures</small><h2>{len(df_view)}</h2></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="card-stat" style="border-top-color:#ffa000"><small>Villages</small><h2>{df_view["Village"].nunique()}</h2></div>', unsafe_allow_html=True)
    inv = df_view["Investissement"].sum() / 1000
    m3.markdown(f'<div class="card-stat" style="border-top-color:#1976d2"><small>Budget (M FCFA)</small><h2>{inv:,.1f}</h2></div>', unsafe_allow_html=True)
    tx_r = int((len(df_view[df_view["Statut"] == "Réalisé"]) / len(df_view)) * 100) if len(df_view) > 0 else 0
    m4.markdown(f'<div class="card-stat" style="border-top-color:#d32f2f"><small>Taux Réalisation</small><h2>{tx_r}%</h2></div>', unsafe_allow_html=True)

    # Graphiques
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.plotly_chart(px.bar(df_view.groupby(['Type', 'Statut']).size().reset_index(name='Nb'), x='Type', y='Nb', color='Statut', barmode='group', color_discrete_map={"Réalisé": "#1b5e20", "En cours": "#ffa000", "Projeté": "#d32f2f"}), use_container_width=True)
    with c_right:
        st.plotly_chart(px.pie(df_view, names='Nature', hole=0.4, title="Public vs Privé"), use_container_width=True)

elif page == "🗺️ Carte Interactive":
    st.header(f"Exploration spatiale : {f_village}")
    
    # Calcul du centre et du zoom
    if not df_view.empty:
        center = [df_view['Lat'].mean(), df_view['Lon'].mean()]
        zoom = 13 if f_village != "Tous les villages" else 11
    else:
        center = [12.95, -16.45]
        zoom = 11

    m = leafmap.Map(center=center, zoom=zoom)
    
    # Fonds de carte
    styles = {"Satellite Hybride": "HYBRID", "Google Terrain": "TERRAIN", "OpenStreetMap": "OpenStreetMap", "CartoDB Dark": "CartoDB.DarkMatter"}
    m.add_basemap(styles.get(map_choice, "OpenStreetMap"))
    
    # Ajout des marqueurs (avec option Cluster pour les 233 points)
    if use_cluster:
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_view.iterrows():
            cfg = map_config.get(row['Type'], {"color": "gray", "icon": "info"})
            pop = f"<b>{row['Type']}</b><br>Village: {row['Village']}<br>Investissement: {row['Investissement']} FCFA"
            folium.Marker(location=[row['Lat'], row['Lon']], popup=pop, icon=folium.Icon(color=cfg['color'], icon=cfg['icon'], prefix='fa')).add_to(marker_cluster)
    else:
        for _, row in df_view.iterrows():
            cfg = map_config.get(row['Type'], {"color": "gray", "icon": "info"})
            pop = f"<b>{row['Type']}</b><br>Village: {row['Village']}"
            m.add_marker(location=[row['Lat'], row['Lon']], popup=pop, icon=folium.Icon(color=cfg['color'], icon=cfg['icon'], prefix='fa'))
    
    m.to_streamlit(height=700)

elif page == "📦 Données Brutes":
    st.header("Registre complet des infrastructures")
    st.dataframe(df_view, use_container_width=True)
    st.download_button("📥 Télécharger CSV", df_view.to_csv(index=False).encode('utf-8'), "djinaky_data.csv")

st.markdown("---")
st.caption(f"SIG Communal Djinaky 2026 | Synchronisation Google Sheets active")
