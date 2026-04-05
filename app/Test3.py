import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import leafmap.foliumap as leafmap
import folium
import os
import requests
from io import BytesIO

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="SIG Djinaky 2026", page_icon="🏥")

# Styles Personnalisés (CSS)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fbf8 0%, #f1f4f9 100%); font-family: 'Segoe UI', sans-serif; }
    .hero-section {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1); margin-bottom: 25px;
        border-left: 10px solid #ffa000;
    }
    .card-stat {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center;
        border-top: 4px solid #1b5e20; transition: transform 0.3s ease;
    }
    .legend-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding: 8px; background: #fff; border-radius: 8px; border: 1px solid #eee; }
    .legend-tag { width: 12px; height: 12px; border-radius: 50%; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CHARGEMENT ET NETTOYAGE DES DONNÉES ---
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
        
        # Correction virgule -> point
        for col in ['Lat', 'Lon']:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Harmonisation
        df['Type'] = df['Type'].astype(str).str.strip().replace({
            'Poste de Sante': 'Poste de Santé',
            'Ecole/Lycee': 'École / Lycée',
            'Marche Communal': 'Marché Communal'
        })
        
        df = df.dropna(subset=['Lat', 'Lon', 'Village'])
        return df, config
    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")
        return pd.DataFrame(), config

df_full, map_config = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #1b5e20;'>O_K_G#95</h2>", unsafe_allow_html=True)
    menu = st.radio("Navigation", ["📊 Dashboard", "🗺️ Carte Interactive", "📋 Registre"])
    
    st.markdown("### 🗺️ STYLE DE CARTE")
    map_style = st.selectbox("Fond de carte", ["Satellite Hybride", "Terrain (Google)", "Standard (OSM)"])
    
    st.markdown("### 🛠️ FILTRES")
    f_village = st.selectbox("Village", ["Tous les villages"] + sorted(list(df_full["Village"].unique())))
    f_type = st.selectbox("Type", ["Tous les types"] + list(map_config.keys()))

    st.markdown("---")
    for k, v in map_config.items():
        count = len(df_full[df_full["Type"] == k])
        st.markdown(f'<div class="legend-row"><div style="display:flex;align-items:center;"><div class="legend-tag" style="background:{v["hex"]};"></div><span style="font-size:12px;">{k}</span></div><b>{count}</b></div>', unsafe_allow_html=True)

# --- 4. LOGIQUE DE FILTRAGE ---
df_display = df_full.copy()
if f_village != "Tous les villages":
    df_display = df_display[df_display["Village"] == f_village]
if f_type != "Tous les types":
    df_display = df_display[df_display["Type"] == f_type]

# --- 5. PAGES ---
if menu == "📊 Dashboard":
    st.markdown(f"""<div class="hero-section"><h1>📍 SIG Communal de Djinaky</h1><p>Vue : {f_village} | {f_type}</p></div>""", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="card-stat"><small>Infrastructures</small><h2>{len(df_display)}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-stat"><small>Villages</small><h2>{df_display["Village"].nunique()}</h2></div>', unsafe_allow_html=True)
    budget = df_display["Investissement"].sum() / 1000 if "Investissement" in df_display.columns else 0
    c3.markdown(f'<div class="card-stat"><small>Budget (M FCFA)</small><h2>{budget:,.1f}</h2></div>', unsafe_allow_html=True)

    st.plotly_chart(px.bar(df_display.groupby(['Type', 'Statut']).size().reset_index(name='Nb'), x='Type', y='Nb', color='Statut', barmode='group', color_discrete_map={"Réalisé": "#1b5e20", "En cours": "#ffa000", "Projeté": "#d32f2f"}), use_container_width=True)

elif menu == "🗺️ Carte Interactive":
    st.header(f"Carte : {f_village} ({len(df_display)} points)")
    
    # Centre dynamique : moyenne de TOUS les points affichés
    if not df_display.empty:
        center = [df_display['Lat'].mean(), df_display['Lon'].mean()]
        zoom_level = 12 if f_village != "Tous les villages" else 11
    else:
        center = [12.95, -16.45]
        zoom_level = 11

    m = leafmap.Map(center=center, zoom=zoom_level)
    
    styles = {"Satellite Hybride": "HYBRID", "Terrain (Google)": "TERRAIN", "Standard (OSM)": "OpenStreetMap"}
    m.add_basemap(styles.get(map_style, "OpenStreetMap"))
    
    # Affiche TOUS les marqueurs présents dans le DataFrame filtré
    for _, row in df_display.iterrows():
        ico_cfg = map_config.get(row['Type'], {"color": "gray", "icon": "info"})
        popup = f"<b>{row['Type']}</b><br>Village: {row['Village']}<br>Statut: {row['Statut']}"
        m.add_marker(location=[row['Lat'], row['Lon']], popup=popup, 
                     icon=folium.Icon(color=ico_cfg['color'], icon=ico_cfg['icon'], prefix='fa'))
    
    m.to_streamlit(height=700)

elif menu == "📋 Registre":
    st.dataframe(df_display, use_container_width=True)
