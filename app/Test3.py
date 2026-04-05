import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import leafmap.foliumap as leafmap
import folium
import os
from io import BytesIO

# --- 1. CONFIGURATION & COMPOSITION VISUELLE (CSS) ---
st.set_page_config(layout="wide", page_title="Géoportail Djinaky 2026", page_icon="🏥")

# Système de suivi des visites (Stockage local)
def update_visit_counter():
    file_path = "stats_visites.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w") as f: f.write("0")
    
    if 'visited' not in st.session_state:
        st.session_state.visited = True
        try:
            with open(file_path, "r+") as f:
                count = int(f.read())
                f.seek(0)
                f.write(str(count + 1))
                f.truncate()
        except: pass

def get_total_visits():
    try:
        with open("stats_visites.txt", "r") as f: return f.read()
    except: return "1"

update_visit_counter()

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f8fbf8 0%, #f1f4f9 100%); font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 2px solid #1b5e20; }
    .hero-section {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15); margin-bottom: 30px;
        border-left: 12px solid #ffa000;
    }
    .card-stat {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center;
        border-top: 5px solid #1b5e20; transition: transform 0.3s ease;
    }
    .card-stat:hover { transform: translateY(-5px); }
    .legend-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 5px; background: #fdfdfd; border-radius: 5px; }
    .legend-tag { width: 14px; height: 14px; border-radius: 3px; margin-right: 10px; }
    .section-title { color: #1b5e20; font-weight: 800; border-bottom: 3px solid #ffa000; display: inline-block; margin-bottom: 20px; padding-bottom: 5px; }
    .stat-visit { text-align:center; background:#f0f2f6; padding:10px; border-radius:10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DONNÉES ---
@st.cache_data
def load_geodata():
    villages = pd.DataFrame({
        "Village": ["Badiana","Baline","Balonguine","Baranlir","Bélaye","Biti Biti","Djinaky","Djinone","Ebinkine","Essom Silathiaye","Kabiline","Karongue","Mongone","Tendine","Wangaran"],
        "Lat": [12.913, 12.917, 12.974, 12.938, 12.900, 13.015, 12.944, 13.000, 12.930, 13.058, 12.954, 12.974, 12.976, 12.934, 13.024],
        "Lon": [-16.438, -16.460, -16.418, -16.374, -16.397, -16.377, -16.464, -16.379, -16.501, -16.390, -16.559, -16.524, -16.465, -16.405, -16.416]
    })
    config = {
        "Poste de Santé": {"color": "red", "hex": "#d32f2f", "icon": "medkit"},
        "École / Lycée": {"color": "purple", "hex": "#7b1fa2", "icon": "graduation-cap"},
        "Forage Hydraulique": {"color": "blue", "hex": "#1976d2", "icon": "tint"},
        "Marché Communal": {"color": "orange", "hex": "#fbc02d", "icon": "shopping-cart"},
        "Ferme Agricole": {"color": "green", "hex": "#388e3c", "icon": "leaf"}
    }
    np.random.seed(42)
    data = pd.DataFrame({
        "ID": range(1, 234),
        "Type": np.random.choice(list(config.keys()), 233),
        "Village": np.random.choice(villages["Village"], 233),
        "Nature": np.random.choice(["Public", "Privé"], 233, p=[0.75, 0.25]),
        "Statut": np.random.choice(["Réalisé", "En cours", "Projeté"], 233),
        "Investissement": np.random.randint(1000, 15000, 233)
    }).merge(villages, on="Village")
    return villages, data, config

villages_df, df_full, map_config = load_geodata()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #1b5e20;'>O_K_G#95</h2>", unsafe_allow_html=True)
    st.caption("Monitoring Communal - Djinaky 2026")
    st.markdown("---")
    
    app_mode = st.selectbox("Menu Principal", ["🏠 Accueil & Dashboard", "🗺️ Carte Interactive", "📥 Exportations"])
    search = st.text_input("🔍 Rechercher un ouvrage", placeholder="Ex: Forage...")

    with st.expander("🌍 FOND DE CARTE", expanded=True):
        basemap_sel = st.radio("Style de vue", ["Standard (OSM)", "Satellite Hybride"], label_visibility="collapsed")

    with st.expander("📊 LÉGENDE / COUCHES", expanded=True):
        for k, v in map_config.items():
            count = len(df_full[df_full["Type"] == k])
            st.markdown(f'<div class="legend-row"><div style="display:flex;align-items:center;"><div class="legend-tag" style="background-color:{v["hex"]};"></div><span style="font-size:13px;">{k}</span></div><b>{count}</b></div>', unsafe_allow_html=True)

    st.markdown("### 🛠️ FILTRES")
    with st.expander("📍 LOCALISATION"):
        f_village = st.selectbox("Village", ["Tous les villages"] + sorted(list(villages_df["Village"])))
    with st.expander("🏗️ TYPE & NATURE"):
        f_type = st.selectbox("Type d'ouvrage", ["Tous les types"] + list(map_config.keys()))
        f_nature = st.radio("Nature", ["Toutes", "Public", "Privé"], horizontal=True)

    # Statistiques d'Audience (Temps Réel)
    st.markdown("---")
    st.markdown("### 👥 AUDIENCE")
    c_v1, c_v2 = st.columns(2)
    c_v1.markdown(f'<div class="stat-visit"><small>Visites</small><br><b style="color:#1b5e20;">{get_total_visits()}</b></div>', unsafe_allow_html=True)
    c_v2.markdown(f'<div class="stat-visit" style="background:#e8f5e9;border:1px solid #1b5e20;"><small>En ligne</small><br><b style="color:#2e7d32;">1</b></div>', unsafe_allow_html=True)
    st.caption("Données de fréquentation anonymisées.")

# --- 4. FILTRAGE ---
df = df_full.copy()
if f_village != "Tous les villages": df = df[df["Village"] == f_village]
if f_type != "Tous les types": df = df[df["Type"] == f_type]
if f_nature != "Toutes": df = df[df["Nature"] == f_nature]
if search: df = df[df["Village"].str.contains(search, case=False) | df["Type"].str.contains(search, case=False)]

# --- 5. PAGES ---
if app_mode == "🏠 Accueil & Dashboard":
    st.markdown(f'<div class="hero-section"><h1 style="margin:0;">📍 SIG Communal de Djinaky</h1><p style="font-size:1.2em;">Plateforme Décisionnelle des Infrastructures de Base</p><hr style="border:0.5px solid rgba(255,255,255,0.2);"><p>Auteur : Omar Goudiaby | Session : Avril 2026</p></div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="card-stat"><small>Infrastructures</small><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-stat" style="border-top-color:#ffa000"><small>Villages</small><h2>{df["Village"].nunique()}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-stat" style="border-top-color:#1976d2"><small>Budget (M FCFA)</small><h2>{df["Investissement"].sum()/1000:,.1f}</h2></div>', unsafe_allow_html=True)
    # ... code précédent (c1, c2, c3) ...
    
    # LE BLOC CORRECTEUR (Lignes 134 et suivantes)
    if len(df) > 0:
        taux_public = int((len(df[df["Nature"] == "Public"]) / len(df)) * 100)
    else:
        taux_public = 0

    c4.markdown(f'<div class="card-stat" style="border-top-color:#d32f2f"><small>Taux Public</small><h2>{taux_public}%</h2></div>', unsafe_allow_html=True)

    # LA LIGNE QUI BUGGE ACTUELLEMENT (Elle doit être alignée avec c4.markdown)
    st.markdown("<br><h3 class='section-title'>📊 Synthèse Territoriale</h3>", unsafe_allow_html=True)
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(px.bar(df.groupby(['Type', 'Statut']).size().reset_index(name='Nombre'), x='Type', y='Nombre', color='Statut', barmode='group', color_discrete_map={"Réalisé": "#1b5e20", "En cours": "#ffa000", "Projeté": "#d32f2f"}), use_container_width=True)
    with col_r:
        st.plotly_chart(px.pie(df, names='Type', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)

elif app_mode == "🗺️ Carte Interactive":
    st.header(f"🗺️ Vue Spatiale : {f_village}")
    m = leafmap.Map(center=[12.95, -16.45], zoom=12, measure_control=True)
    if basemap_sel == "Satellite Hybride": m.add_basemap("HYBRID")
    
    for _, row in df.iterrows():
        popup = f"<div style='font-family:sans-serif;'><b>{row['Type']}</b><hr>Village: {row['Village']}<br>Nature: {row['Nature']}<br>Statut: {row['Statut']}</div>"
        m.add_marker(location=[row['Lat'], row['Lon']], popup=popup, icon=folium.Icon(color=map_config[row['Type']]['color'], icon=map_config[row['Type']]['icon'], prefix='fa'))
    m.to_streamlit(height=700)

elif app_mode == "📥 Exportations":
    st.header("📥 Extraction de Données")
    st.dataframe(df.drop(columns=['Lat', 'Lon']), use_container_width=True)
    c_ex1, c_ex2 = st.columns(2)
    c_ex1.download_button("💾 Exporter CSV", df.to_csv(index=False).encode('utf-8'), "sig_djinaky.csv", "text/csv")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False)
    c_ex2.download_button("📊 Exporter Excel", output.getvalue(), "sig_djinaky.xlsx")

st.markdown("---")
st.caption("🏠 **SIG Djinaky 2026** | Système d'Information Géographique Communal | © Mairie de Djinaky")
