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
        border-top: 4px solid #1b5e20;
    }
    .legend-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding: 8px; background: #fff; border-radius: 8px; border: 1px solid #eee; }
    .legend-tag { width: 12px; height: 12px; border-radius: 50%; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FONCTION DE CHARGEMENT ET NETTOYAGE ---
@st.cache_data(ttl=600)
def load_data():
    # URL de ton Google Sheet publié en XLSX
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTI7qqNBuvYmXBPB5qCS0COBPBf4vtHHymhI4d4P3_ATD8kX-Tqw5Sv3IMbv0M6u1em4l_fQzclGRLp/pub?output=xlsx"
    
    # Dictionnaire de configuration visuelle
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
        
        # Nettoyage des noms de colonnes (suppression des espaces)
        df.columns = df.columns.str.strip()
        
        # --- CORRECTEUR DE DONNÉES ---
        # 1. Gestion des virgules dans les coordonnées (Lat/Lon)
        for col in ['Lat', 'Lon']:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 2. Harmonisation des types d'infrastructures (Accents et Orthographe)
        df['Type'] = df['Type'].astype(str).str.strip().replace({
            'Poste de Sante': 'Poste de Santé',
            'Ecole/Lycee': 'École / Lycée',
            'Marche Communal': 'Marché Communal'
        })
        
        # 3. Conversion investissement en nombre
        if 'Investissement' in df.columns:
            df['Investissement'] = pd.to_numeric(df['Investissement'], errors='coerce').fillna(0)

        # Suppression des lignes invalides
        df = df.dropna(subset=['Lat', 'Lon', 'Village'])
        
        # Moyennes par village pour le centrage de la carte
        villages = df.groupby('Village')[['Lat', 'Lon']].mean().reset_index()
        
        return villages, df, config
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la lecture des données : {e}")
        return pd.DataFrame(), pd.DataFrame(), config

villages_df, df_full, map_config = load_data()

# --- 3. BARRE LATÉRALE (FILTRES) ---
with st.sidebar:
    st.markdown("<h2 style='color: #1b5e20;'>O_K_G#95</h2>", unsafe_allow_html=True)
    st.caption("Système de Suivi Djinaky 2026")
    st.markdown("---")
    
    menu = st.radio("Navigation", ["📊 Dashboard", "🗺️ Carte Interactive", "📋 Liste & Export"])
    
    st.markdown("### 🛠️ Filtres")
    v_list = ["Tous les villages"] + sorted(list(villages_df["Village"].unique()))
    f_village = st.selectbox("Sélectionner un village", v_list)
    
    t_list = ["Tous les types"] + list(map_config.keys())
    f_type = st.selectbox("Type d'infrastructure", t_list)

    st.markdown("---")
    st.markdown("### 📊 État du Patrimoine")
    for k, v in map_config.items():
        count = len(df_full[df_full["Type"] == k])
        st.markdown(f'''
            <div class="legend-row">
                <div style="display:flex; align-items:center;">
                    <div class="legend-tag" style="background:{v["hex"]};"></div>
                    <span style="font-size:12px;">{k}</span>
                </div>
                <b style="font-size:13px;">{count}</b>
            </div>
        ''', unsafe_allow_html=True)

# --- 4. LOGIQUE DE FILTRAGE ---
df = df_full.copy()
if f_village != "Tous les villages":
    df = df[df["Village"] == f_village]
if f_type != "Tous les types":
    df = df[df["Type"] == f_type]

# --- 5. AFFICHAGE DES PAGES ---

# --- PAGE 1 : DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown(f"""
        <div class="hero-section">
            <h1 style="margin:0;">📍 SIG Communal de Djinaky</h1>
            <p style="font-size:1.1em; opacity:0.9;">Analyse temps-réel : {f_village if f_village != "Tous les villages" else "Ensemble de la commune"}</p>
        </div>
    """, unsafe_allow_html=True)

    # Indicateurs clés
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="card-stat"><small>Infrastructures</small><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-stat" style="border-top-color:#ffa000"><small>Villages</small><h2>{df["Village"].nunique()}</h2></div>', unsafe_allow_html=True)
    budget_total = df["Investissement"].sum() / 1000
    c3.markdown(f'<div class="card-stat" style="border-top-color:#1976d2"><small>Budget (M FCFA)</small><h2>{budget_total:,.1f}</h2></div>', unsafe_allow_html=True)
    tx_public = int((len(df[df["Nature"] == "Public"]) / len(df)) * 100) if len(df) > 0 else 0
    c4.markdown(f'<div class="card-stat" style="border-top-color:#d32f2f"><small>Taux Public</small><h2>{tx_public}%</h2></div>', unsafe_allow_html=True)

    # Graphiques
    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        fig_bar = px.bar(df.groupby(['Type', 'Statut']).size().reset_index(name='Nombre'), 
                         x='Type', y='Nombre', color='Statut', barmode='group',
                         title="Avancement des travaux par secteur",
                         color_discrete_map={"Réalisé": "#1b5e20", "En cours": "#ffa000", "Projeté": "#d32f2f"})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_r:
        fig_pie = px.pie(df, names='Type', hole=0.5, title="Répartition par type",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

# --- PAGE 2 : CARTE ---
elif menu == "🗺️ Carte Interactive":
    st.header(f"📍 Cartographie : {f_village}")
    
    # Calcul du centre
    if not df.empty:
        center = [df['Lat'].mean(), df['Lon'].mean()]
    else:
        center = [12.95, -16.45]

    m = leafmap.Map(center=center, zoom=12, measure_control=True)
    m.add_basemap("HYBRID")
    
    for _, row in df.iterrows():
        icon_info = map_config.get(row['Type'], {"color": "gray", "icon": "info-circle"})
        popup_html = f"""
            <div style="font-family: Arial; width: 180px;">
                <h4 style="margin:0; color:#1b5e20;">{row['Type']}</h4>
                <hr style="margin:5px 0;">
                <b>Village :</b> {row['Village']}<br>
                <b>Statut :</b> {row['Statut']}<br>
                <b>Nature :</b> {row['Nature']}
            </div>
        """
        m.add_marker(location=[row['Lat'], row['Lon']], 
                     popup=popup_html, 
                     icon=folium.Icon(color=icon_info['color'], icon=icon_info['icon'], prefix='fa'))
    
    m.to_streamlit(height=700)

# --- PAGE 3 : EXPORT ---
elif menu == "📋 Liste & Export":
    st.header("🗂️ Registre des infrastructures")
    st.dataframe(df.drop(columns=['Lat', 'Lon']), use_container_width=True)
    
    c_d1, c_d2 = st.columns(2)
    csv = df.to_csv(index=False).encode('utf-8')
    c_d1.download_button("📥 Télécharger en CSV", csv, "sig_djinaky.csv", "text/csv")
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    c_d2.download_button("📥 Télécharger en Excel", output.getvalue(), "sig_djinaky.xlsx")

st.markdown("---")
st.caption(f"🏠 SIG Communal Djinaky 2026 | Omar Goudiaby | Données issues de Google Sheets")
