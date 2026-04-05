import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import leafmap.foliumap as leafmap
import folium
from io import BytesIO

# --- 1. CONFIGURATION & DESIGN PERSONNALISÉ ---
st.set_page_config(layout="wide", page_title="SIG Communal Djinaky", page_icon="🌍")

# Personnalisation de la couleur de fond (Vert Casamance Soft)
st.markdown("""
    <style>
    /* Fond de la page principale */
    .stApp {
        background-color: #f0f4f1;
    }
    /* Barre latérale */
    [data-testid="stSidebar"] {
        background-color: #1b5e20;
        color: white;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    /* Conteneurs de statistiques (Cartes) */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #2e7d32;
    }
    .description-box {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border-left: 8px solid #ffa000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        color: #2c3e50;
    }
    .section-header {
        font-weight: bold;
        font-size: 18px;
        margin-top: 20px;
        color: #ffffff;
        border-bottom: 1px solid #4caf50;
        padding-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GÉNÉRATION DES DONNÉES (DJINAKY) ---
@st.cache_data
def get_data():
    villages_df = pd.DataFrame({
        "Village": ["Badiana","Baline","Balonguine","Baranlir","Bélaye","Biti Biti","Djinaky","Djinone","Ebinkine","Essom Silathiaye","Kabiline","Karongue","Mongone","Tendine","Wangaran"],
        "Lat": [12.913023,12.917847,12.974478,12.938795,12.90066,13.015207,12.944582,13.000269,12.930223,13.0582,12.954081,12.974728,12.976757,12.93486,13.024063],
        "Lon": [-16.438224,-16.460029,-16.418417,-16.374767,-16.397459,-16.377685,-16.464277,-16.379981,-16.501491,-16.39004,-16.559737,-16.524608,-16.465599,-16.405842,-16.416864]
    })
    
    config = {
        "Ecole": {"color": "purple", "hex": "#9c27b0", "icon": "graduation-cap"},
        "Forage": {"color": "blue", "hex": "#2196f3", "icon": "tint"},
        "Lampadaire solaire": {"color": "orange", "hex": "#ff9800", "icon": "lightbulb"},
        "Ferme agricole": {"color": "green", "hex": "#4caf50", "icon": "leaf"},
        "Poste de santé": {"color": "red", "hex": "#f44336", "icon": "medkit"}
    }
    
    np.random.seed(42)
    infra = pd.DataFrame({
        "ID": range(1, 251),
        "Village": np.random.choice(villages_df["Village"], 250),
        "Type": np.random.choice(list(config.keys()), 250),
        "Statut": np.random.choice(["Réalisé", "En cours", "Projeté"], 250, p=[0.4, 0.3, 0.3]),
        "Nature": np.random.choice(["Public", "Privé"], 250),
        "Investissement": np.random.randint(500, 8500, 250)
    }).merge(villages_df, on="Village")
    
    return villages_df, infra, config

villages_df, df_full, config = get_data()

# --- 3. BARRE LATÉRALE (NAVIGATION & FILTRES) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Flag_of_Senegal.svg/200px-Flag_of_Senegal.svg.png", width=80)
    st.title("Géoportail Djinaky")
    st.markdown("---")
    
    app_mode = st.radio("MENU PRINCIPAL", ["🏠 Accueil", "🗺️ Carte Interactive", "📊 Analyses & Graphiques", "📥 Exportations"])
    
    st.markdown('<p class="section-header">FILTRES GLOBAUX</p>', unsafe_allow_html=True)
    # Sélection de TOUS par défaut comme demandé
    f_type = st.multiselect("Infrastructures", options=list(config.keys()), default=list(config.keys()))
    f_statut = st.multiselect("Statut des projets", options=["Réalisé", "En cours", "Projeté"], default=["Réalisé", "En cours", "Projeté"])
    
    st.markdown("---")
    st.caption("Conçu pour la mairie de Djinaky © 2026")

# Application du filtrage
df = df_full[(df_full['Type'].isin(f_type)) & (df_full['Statut'].isin(f_statut))]

# --- 4. LOGIQUE DES PAGES ---

if app_mode == "🏠 Accueil":
    st.title("Système d'Information Géographique de Djinaky")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div class="description-box">
            <h3>📍 Présentation de la Commune</h3>
            Située dans le département de <b>Bignona</b>, la commune de <b>Djinaky</b> est un carrefour stratégique de la Basse-Casamance. 
            Elle regroupe des villages dynamiques engagés dans une transition vers une agriculture moderne et un accès universel aux services de base.
            <br><br>
            <b>Ce portail compile actuellement :</b>
            <ul>
                <li>{len(df_full)} infrastructures recensées.</li>
                <li>{villages_df.shape[0]} villages cartographiés.</li>
                <li>Suivi en temps réel des projets d'investissement public.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("### Indicateurs de Performance")
        c1, c2, c3 = st.columns(3)
        c1.metric("Projets Affichés", len(df))
        c2.metric("Investissement Total", f"{df['Investissement'].sum():,} k FCFA")
        c3.metric("Villages Couverts", df['Village'].nunique())

    with col2:
        # Graphique rapide d'accueil
        fig_intro = px.pie(df, names='Statut', color='Statut', hole=0.6,
                           color_discrete_map={"Réalisé":"#2e7d32", "En cours":"#ffa000", "Projeté":"#d32f2f"})
        fig_intro.update_layout(showlegend=False, title="État Global des Projets")
        st.plotly_chart(fig_intro, use_container_width=True)

elif app_mode == "🗺️ Carte Interactive":
    st.header("🗺️ Cartographie Multi-échelles")
    
    # Choix du fond de carte
    base = st.selectbox("Fond de carte", ["Satellite Hybride", "OpenStreetMap", "Terrain"])
    
    m = leafmap.Map(center=[12.95, -16.45], zoom=12)
    
    if base == "Satellite Hybride":
        m.add_basemap("HYBRID")
    elif base == "Terrain":
        m.add_basemap("TERRAIN")

    # Affichage de TOUS les points filtrés
    for _, row in df.iterrows():
        m.add_marker(
            location=[row['Lat'], row['Lon']],
            popup=f"<b>{row['Village']}</b><br>{row['Type']}<br>{row['Statut']}",
            icon=folium.Icon(color=config[row['Type']]['color'], icon=config[row['Type']]['icon'], prefix='fa')
        )
    
    m.to_streamlit(height=700)

elif app_mode == "📊 Analyses & Graphiques":
    st.header("📊 Tableaux de Bord Analytiques")
    
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        st.subheader("Histogramme : Infrastructures par Village")
        fig1 = px.bar(df.groupby(['Village', 'Statut']).size().reset_index(name='Compte'), 
                     x='Village', y='Compte', color='Statut', barmode='stack',
                     color_discrete_map={"Réalisé":"#2e7d32", "En cours":"#ffa000", "Projeté":"#d32f2f"})
        st.plotly_chart(fig1, use_container_width=True)

    with row1_col2:
        st.subheader("Diagramme Circulaire : Types d'Ouvrages")
        fig2 = px.pie(df, names='Type', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    
    row2_col1, row2_col2 = st.columns([2, 1])
    with row2_col1:
        st.subheader("Analyse Financière : Investissement par Type")
        fig3 = px.box(df, x='Type', y='Investissement', color='Type', points="all")
        st.plotly_chart(fig3, use_container_width=True)
    with row2_col2:
        st.subheader("Nature des Projets")
        fig4 = px.pie(df, names='Nature', color_discrete_sequence=['#1b5e20', '#a5d6a7'])
        st.plotly_chart(fig4, use_container_width=True)

elif app_mode == "📥 Exportations":
    st.header("📥 Centre d'Exportation")
    st.write("Téléchargez les données filtrées pour vos rapports administratifs ou pour QGIS.")
    
    c_e1, c_e2 = st.columns(2)
    
    # CSV
    csv = df.to_csv(index=False).encode('utf-8')
    c_e1.download_button("📥 Télécharger en CSV", data=csv, file_name="sig_djinaky_complet.csv", mime='text/csv')
    
    # Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    c_e2.download_button("📥 Télécharger en EXCEL", data=output.getvalue(), file_name="sig_djinaky_complet.xlsx")
    
    st.markdown("---")
    st.subheader("Aperçu de la base de données")
    st.dataframe(df.drop(columns=['Lat', 'Lon']), use_container_width=True)
    
    st.info("💡 Pour un export **PNG** ou **TIFF** des graphiques, utilisez l'icône appareil photo 'Download plot as a png' située au-dessus de chaque graphique.")