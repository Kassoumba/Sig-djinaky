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
    .card-stat:hover { transform: translateY(-3px); }
    .legend-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding: 8px; background: #fff; border-radius: 8px; border: 1px solid #eee; }
    .legend-tag { width: 12px; height: 12px; border-radius: 50%; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CHARGEMENT ET NETTOYAGE DES DONNÉES ---
@st.cache_data(ttl=300) # Rafraîchissement toutes les 5 minutes
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
        
        # Correcteur de coordonnées (virgule -> point)
        for col in ['Lat', 'Lon']:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Harmonisation des types
        df['Type'] = df['Type'].astype(str).str.strip().replace({
            'Poste de Sante': 'Poste de Santé',
            'Ecole/Lycee': 'École / Lycée',
            'Marche Communal': 'Marché Communal'
        })
        
        df['Investissement'] = pd.to_numeric(df['Investissement'], errors='coerce').fillna(0)
        df = df.dropna(subset=['Lat', 'Lon', 'Village'])
        
        villages = df.groupby('Village')[['Lat', 'Lon']].mean().reset_index()
        return villages, df, config
    except Exception as e:
        st.error(f"⚠️ Erreur de données : {e}")
        return pd.DataFrame(), pd.DataFrame(), config

villages_df, df_full, map_config = load_data()

# --- 3. SIDEBAR (FILTRES & FONDS DE CARTE) ---
with st.sidebar:
    st.markdown("<h2 style='color: #1b5e20;'>O_K_G#95</h2>", unsafe_allow_html=True)
    st.caption("Monitoring Djinaky 2026")
    st.markdown("---")
    
    menu = st.radio("Navigation", ["📊 Dashboard", "🗺️ Carte Interactive", "📋 Registre & Export"])
    
    st.markdown("### 🗺️ STYLE DE CARTE")
    map_style = st.selectbox("Fond de carte", 
                             ["Satellite Hybride", "Terrain (Google)", "Standard (OSM)", "Sombre (CartoDB)"])
    
    st.markdown("### 🛠️ FILTRES")
    v_list = ["Tous les villages"] + sorted(list(villages_df["Village"].unique()))
    f_village = st.selectbox("Sélectionner un village", v_list)
    
    t_list = ["Tous les types"] + list(map_config.keys())
    f_type = st.selectbox("Type d'infrastructure", t_list)

    st.markdown("---")
    st.markdown("### 📊 STATISTIQUES")
    for k, v in map_config.items():
        count = len(df_full[df_full["Type"] == k])
        st.markdown(f'<div class="legend-row"><div style="display:flex;align-items:center;"><div class="legend-tag" style="background:{v["hex"]};"></div><span style="font-size:12px;">{k}</span></div><b>{count}</b></div>', unsafe_allow_html=True)

# --- 4. LOGIQUE DE FILTRAGE ---
df = df_full.copy()
if f_village != "Tous les villages":
    df = df[df["Village"] == f_village]
if f_type != "Tous les types":
    df = df[df["Type"] == f_type]

# --- 5. PAGES ---

if menu == "📊 Dashboard":
    st.markdown(f"""<div class="hero-section"><h1 style="margin:0;">📍 SIG Communal de Djinaky</h1><p>Analyse territoriale dynamique | Source : Google Sheets</p></div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="card-stat"><small>Infrastructures</small><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-stat" style="border-top-color:#ffa000"><small>Villages</small><h2>{df["Village"].nunique()}</h2></div>', unsafe_allow_html=True)
    budget = df["Investissement"].sum() / 1000
    c3.markdown(f'<div class="card-stat" style="border-top-color:#1976d2"><small>Budget (M FCFA)</small><h2>{budget:,.1f}</h2></div>', unsafe_allow_html=True)
    tx_p = int((len(df[df["Nature"] == "Public"]) / len(df)) * 100) if len(df) > 0 else 0
    c4.markdown(f'<div class="card-stat" style="border-top-color:#d32f2f"><small>Taux Public</small><h2>{tx_p}%</h2></div>', unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(px.bar(df.groupby(['Type', 'Statut']).size().reset_index(name='Nb'), x='Type', y='Nb', color='Statut', barmode='group', title="État d'avancement par secteur", color_discrete_map={"Réalisé": "#1b5e20", "En cours": "#ffa000", "Projeté": "#d32f2f"}), use_container_width=True)
    with col_r:
        st.plotly_chart(px.pie(df, names='Nature', hole=0.5, title="Public vs Privé"), use_container_width=True)

elif menu == "🗺️ Carte Interactive":
    st.header(f"Vue Spatiale : {f_village}")
    center = [df['Lat'].mean(), df['Lon'].mean()] if not df.empty else [12.95, -16.45]
    
    m = leafmap.Map(center=center, zoom=12, measure_control=True)
    
    # Gestion du choix du fond de carte
    styles = {
        "Satellite Hybride": "HYBRID",
        "Terrain (Google)": "TERRAIN",
        "Standard (OSM)": "OpenStreetMap",
        "Sombre (CartoDB)": "CartoDB.DarkMatter"
    }
    m.add_basemap(styles.get(map_style, "OpenStreetMap"))
    
    for _, row in df.iterrows():
        ico = map_config.get(row['Type'], {"color": "gray", "icon": "info"})
        popup = f"<b>{row['Type']}</b><hr>Village: {row['Village']}<br>Statut: {row['Statut']}"
        m.add_marker(location=[row['Lat'], row['Lon']], popup=popup, icon=folium.Icon(color=ico['color'], icon=ico['icon'], prefix='fa'))
    
    m.to_streamlit(height=700)

elif menu == "📋 Registre & Export":
    st.header("🗂️ Liste des infrastructures")
    st.dataframe(df.drop(columns=['Lat', 'Lon']), use_container_width=True)
    
    c_d1, c_d2 = st.columns(2)
    c_d1.download_button("📥 Export CSV", df.to_csv(index=False).encode('utf-8'), "sig_djinaky.csv")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as wr:
        df.to_excel(wr, index=False)
    c_d2.download_button("📥 Export Excel", output.getvalue(), "sig_djinaky.xlsx")

st.markdown("---")
st.caption(f"🏠 SIG Djinaky 2026 | Omar Goudiaby | Base de données Excel synchronisée")
