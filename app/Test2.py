import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import leafmap.foliumap as leafmap
import folium
from io import BytesIO

# --- 1. CONFIGURATION & COMPOSITION VISUELLE (CSS) ---
st.set_page_config(layout="wide", page_title="Géoportail Djinaky 2026", page_icon="🏥")

st.markdown("""
    <style>
    /* Fond global et typographie */
    .stApp {
        background: linear-gradient(135deg, #f8fbf8 0%, #f1f4f9 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Barre latérale (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px solid #1b5e20;
    }
    
    /* Bannière d'accueil "Hero Section" */
    .hero-section {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 30px;
        border-left: 12px solid #ffa000;
    }

    /* Cartes de statistiques (Cards) */
    .card-stat {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 5px solid #1b5e20;
        transition: transform 0.3s ease;
    }
    .card-stat:hover {
        transform: translateY(-5px);
    }

    /* Légende personnalisée dans la sidebar */
    .legend-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding: 5px;
        background: #fdfdfd;
        border-radius: 5px;
    }
    .legend-tag {
        width: 14px;
        height: 14px;
        border-radius: 3px;
        margin-right: 10px;
    }
    
    /* Titres */
    .section-title {
        color: #1b5e20;
        font-weight: 800;
        border-bottom: 3px solid #ffa000;
        display: inline-block;
        margin-bottom: 20px;
        padding-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GÉNÉRATION DES DONNÉES (SIMULATION PROFESSIONNELLE) ---
@st.cache_data
def load_geodata():
    # Villages de la commune
    villages = pd.DataFrame({
        "Village": ["Badiana","Baline","Balonguine","Baranlir","Bélaye","Biti Biti","Djinaky","Djinone","Ebinkine","Essom Silathiaye","Kabiline","Karongue","Mongone","Tendine","Wangaran"],
        "Lat": [12.913, 12.917, 12.974, 12.938, 12.900, 13.015, 12.944, 13.000, 12.930, 13.058, 12.954, 12.974, 12.976, 12.934, 13.024],
        "Lon": [-16.438, -16.460, -16.418, -16.374, -16.397, -16.377, -16.464, -16.379, -16.501, -16.390, -16.559, -16.524, -16.465, -16.405, -16.416]
    })
    
    # Configuration des thématiques (Inspiré du Bénin)
    config = {
        "Poste de Santé": {"color": "red", "hex": "#d32f2f", "icon": "medkit"},
        "École / Lycée": {"color": "purple", "hex": "#7b1fa2", "icon": "graduation-cap"},
        "Forage Hydraulique": {"color": "blue", "hex": "#1976d2", "icon": "tint"},
        "Marché Communal": {"color": "orange", "hex": "#fbc02d", "icon": "shopping-cart"},
        "Ferme Agricole": {"color": "green", "hex": "#388e3c", "icon": "leaf"}
    }
    
    # Génération de 233 infrastructures (comme dans votre exemple)
    np.random.seed(42)
    types_list = list(config.keys())
    data = pd.DataFrame({
        "ID": range(1, 234),
        "Type": np.random.choice(types_list, 233),
        "Village": np.random.choice(villages["Village"], 233),
        "Nature": np.random.choice(["Public", "Privé"], 233, p=[0.75, 0.25]),
        "Statut": np.random.choice(["Réalisé", "En cours", "Projeté"], 233),
        "Investissement": np.random.randint(1000, 15000, 233)
    }).merge(villages, on="Village")
    
    return villages, data, config

villages_df, df_full, map_config = load_geodata()

# --- 3. SIDEBAR (INTERFACE GÉOPORTAIL) ---
with st.sidebar:
    st.markdown("<h2 style='color: #1b5e20;'>🇸🇳 GÉOPORTAIL</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666;'>Infrastructures de Djinaky</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation principale
    app_mode = st.selectbox("Navigation", ["🏠 Accueil & Dashboard", "🗺️ Carte Interactive", "📥 Exportations"])
    
    # Recherche rapide
    search = st.text_input("🔍 Recherche rapide", placeholder="Ex: Poste de santé...")

    # Menu déroulant : Fond de carte
    with st.expander("🌍 FOND DE CARTE", expanded=True):
        basemap_sel = st.radio("Style", ["Standard (OSM)", "Satellite Hybride"], label_visibility="collapsed")

    # Légende Dynamique (Composition de couleurs)
    with st.expander("📊 LÉGENDE / COUCHES", expanded=True):
        for k, v in map_config.items():
            count = len(df_full[df_full["Type"] == k])
            st.markdown(f"""
                <div class="legend-row">
                    <div style="display:flex; align-items:center;">
                        <div class="legend-tag" style="background-color:{v['hex']};"></div>
                        <span style="font-size:13px; color:#333;">{k}</span>
                    </div>
                    <span style="font-weight:bold; color:#1b5e20;">{count}</span>
                </div>
            """, unsafe_allow_html=True)

    # Filtres Menus Déroulants
    st.markdown("### 🛠️ FILTRES")
    with st.expander("📍 LOCALISATION"):
        f_village = st.selectbox("Village cible", ["Tous les villages"] + sorted(list(villages_df["Village"])))
    
    with st.expander("🏗️ TYPE & NATURE"):
        f_type = st.selectbox("Type d'ouvrage", ["Tous les types"] + list(map_config.keys()))
        f_nature = st.radio("Nature", ["Toutes", "Public", "Privé"], horizontal=True)

    # Bas de sidebar : Actions
    st.markdown("---")
    st.caption("© 2026 - Commune de Djinaky")

# --- 4. LOGIQUE DE FILTRAGE ---
df = df_full.copy()
if f_village != "Tous les villages":
    df = df[df["Village"] == f_village]
if f_type != "Tous les types":
    df = df[df["Type"] == f_type]
if f_nature != "Toutes":
    df = df[df["Nature"] == f_nature]
if search:
    df = df[df["Village"].str.contains(search, case=False) | df["Type"].str.contains(search, case=False)]

# --- 5. PAGES ---

if app_mode == "🏠 Accueil & Dashboard":
    # Hero Banner
    st.markdown("""
        <div class="hero-section">
            <h1 style='margin:0;'>📍 Géoportail Communal de Djinaky</h1>
            <p style='font-size:1.2em; opacity:0.9;'>Suivi et Planification des Infrastructures Sanitaires et Sociales</p>
            <hr style='border:0.5px solid rgba(255,255,255,0.2);'>
            <p>Piloter le développement local par la donnée géographique précise.</p>
        </div>
    """, unsafe_allow_html=True)

    # Composition de Cartes de Statistiques
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="card-stat"><small>Infrastructures</small><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-stat" style="border-top-color:#ffa000"><small>Villages</small><h2>{df["Village"].nunique()}</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-stat" style="border-top-color:#1976d2"><small>Investissement (M)</small><h2>{df["Investissement"].sum()/1000:,.1f}</h2></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card-stat" style="border-top-color:#d32f2f"><small>Taux Public</small><h2>{int((len(df[df["Nature"]=="Public"])/len(df))*100)}%</h2></div>', unsafe_allow_html=True)

    st.markdown("<br><h3 class='section-title'>📊 Analyses Globales</h3>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        fig_bar = px.bar(df.groupby(['Type', 'Statut']).size().reset_index(name='Nombre'), 
                        x='Type', y='Nombre', color='Statut', barmode='group',
                        color_discrete_map={"Réalisé": "#1b5e20", "En cours": "#ffa000", "Projeté": "#d32f2f"},
                        title="État d'avancement par thématique")
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_r:
        fig_pie = px.pie(df, names='Type', hole=0.5, title="Répartition des ouvrages")
        st.plotly_chart(fig_pie, use_container_width=True)

elif app_mode == "🗺️ Carte Interactive":
    st.header(f"🗺️ Cartographie : {f_village}")
    
    # Création de la carte
    m = leafmap.Map(center=[12.95, -16.45], zoom=12, draw_control=False, measure_control=True)
    
    if basemap_sel == "Satellite Hybride":
        m.add_basemap("HYBRID")
    
    for _, row in df.iterrows():
        popup = f"""
        <div style='font-family:sans-serif; min-width:150px;'>
            <h4 style='color:#1b5e20; margin-bottom:5px;'>{row['Type']}</h4>
            <hr>
            <b>Village:</b> {row['Village']}<br>
            <b>Nature:</b> {row['Nature']}<br>
            <b>Statut:</b> {row['Statut']}
        </div>
        """
        m.add_marker(
            location=[row['Lat'], row['Lon']],
            popup=popup,
            icon=folium.Icon(color=map_config[row['Type']]['color'], icon=map_config[row['Type']]['icon'], prefix='fa')
        )
    
    m.to_streamlit(height=700)

elif app_mode == "📥 Exportations":
    st.header("📥 Extraction de données")
    st.write("Téléchargez les données filtrées au format CSV ou Excel pour vos rapports.")
    
    st.dataframe(df.drop(columns=['Lat', 'Lon']), use_container_width=True)
    
    c_ex1, c_ex2 = st.columns(2)
    csv = df.to_csv(index=False).encode('utf-8')
    c_ex1.download_button("💾 Exporter en CSV", data=csv, file_name="sig_djinaky.csv", mime="text/csv")
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    c_ex2.download_button("📊 Exporter en Excel", data=output.getvalue(), file_name="sig_djinaky.xlsx")

# --- FOOTER ---
st.markdown("---")
st.caption("🏠 **SIG Djinaky v4.0** | Géoportail de suivi des infrastructures sanitaires et sociales | Développé pour la commune en 2026.")