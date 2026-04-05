import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from geopy.distance import geodesic
import leafmap.foliumap as leafmap
import folium

# --- 1. CONFIGURATION ET STYLES ---
st.set_page_config(layout="wide", page_title="SIG Djinaky v3.0")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DONNÉES ---
@st.cache_data
def load_data():
    villages_df = pd.DataFrame({
        "Village": ["Badiana","Baline","Balonguine","Baranlir","Bélaye","Biti Biti","Djinaky","Djinone","Ebinkine","Essom Silathiaye","Kabiline","Karongue","Mongone","Tendine","Wangaran"],
        "Lat": [12.913023,12.917847,12.974478,12.938795,12.90066,13.015207,12.944582,13.000269,12.930223,13.0582,12.954081,12.974728,12.976757,12.93486,13.024063],
        "Lon": [-16.438224,-16.460029,-16.418417,-16.374767,-16.397459,-16.377685,-16.464277,-16.379981,-16.501491,-16.39004,-16.559737,-16.524608,-16.465599,-16.405842,-16.416864]
    })

    map_config = {
        "Ecole": {"color": "purple", "icon": "graduation-cap"},
        "Forage": {"color": "blue", "icon": "tint"},
        "Lampadaire solaire": {"color": "cadetblue", "icon": "lightbulb"},
        "Ferme agricole": {"color": "green", "icon": "leaf"},
        "Poste de santé": {"color": "red", "icon": "medkit"}
    }

    np.random.seed(123)
    types = list(map_config.keys())
    statuts = ["Réalisé", "En cours", "Projeté"]
    
    infra = pd.DataFrame({
        "ID": range(1, 251),
        "Village": np.random.choice(villages_df["Village"], 250),
        "Type": np.random.choice(types, 250),
        "Statut": np.random.choice(statuts, 250, p=[0.4, 0.3, 0.3]),
        "Investissement": np.random.randint(500, 5000, 250)
    }).merge(villages_df, on="Village")
    
    return villages_df, infra, map_config

villages_df, infra_df, map_config = load_data()

# --- 3. SIDEBAR (FILTRES) ---
st.sidebar.title("SIG Djinaky v3.0")
menu = st.sidebar.radio("Navigation", ["Tableau de bord", "Carte & Itinéraires", "Focus Village", "Données RAW"])

st.sidebar.markdown("---")
basemap_option = st.sidebar.selectbox("Fond de carte", ["Plan Clair", "Satellite"])
f_type = st.sidebar.selectbox("Type infrastructure", ["Tous"] + list(map_config.keys()))
f_statut = st.sidebar.selectbox("Statut du projet", ["Tous", "Réalisé", "En cours", "Projeté"])

# Filtrage global
df_filtered = infra_df.copy()
if f_type != "Tous":
    df_filtered = df_filtered[df_filtered["Type"] == f_type]
if f_statut != "Tous":
    df_filtered = df_filtered[df_filtered["Statut"] == f_statut]

# --- 4. LOGIQUE DES ONGLETS ---

if menu == "Tableau de bord":
    st.header("📊 Indicateurs de Performance")
    
    # Value Boxes
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Projets", len(df_filtered))
    c2.metric("Réalisés", len(df_filtered[df_filtered["Statut"] == "Réalisé"]))
    c3.metric("Budget Total", f"{df_filtered['Investissement'].sum():,} k FCFA")
    
    # Graphique principal
    st.subheader("Répartition des projets par statut")
    chart_data = df_filtered.groupby(['Type', 'Statut']).size().reset_index(name='Nombre')
    fig = px.bar(chart_data, x='Type', y='Nombre', color='Statut', barmode='group',
                 color_discrete_map={"Réalisé": "#27ae60", "En cours": "#f1c40f", "Projeté": "#e74c3c"})
    st.plotly_chart(fig, use_container_width=True)

elif menu == "Carte & Itinéraires":
    st.header("🗺️ Cartographie Interactive")
    
    col_map, col_tools = st.columns([3, 1])
    
    with col_tools:
        st.subheader("Mesures")
        v1 = st.selectbox("Départ", villages_df["Village"], index=7) # Djinone
        v2 = st.selectbox("Arrivée", villages_df["Village"], index=6) # Djinaky
        dist_mode = st.radio("Mode :", ["Vol d'oiseau", "Route (Estimation)"])
        
        # Calcul Distance
        p1 = villages_df[villages_df["Village"] == v1][["Lat", "Lon"]].values[0]
        p2 = villages_df[villages_df["Village"] == v2][["Lat", "Lon"]].values[0]
        dist = geodesic(p1, p2).km
        st.write(f"### {dist:.2f} km")
    
    with col_map:
        m = leafmap.Map(center=[12.95, -16.45], zoom=11)
        
        # Fond de carte
        if basemap_option == "Satellite":
            m.add_tile_layer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", name="Satellite", attribution="ESRI")
        
        # Ajout des marqueurs (Infrastructures)
        for _, row in df_filtered.iterrows():
            popup_html = f"<b>{row['Village']}</b><br>{row['Type']}<br>Statut: {row['Statut']}<br>Invest: {row['Investissement']}k"
            m.add_marker(
                location=[row['Lat'], row['Lon']],
                popup=popup_html,
                tooltip=row['Village'],
                icon=folium.Icon(color=map_config[row['Type']]['color'], icon=map_config[row['Type']]['icon'], prefix='fa')
            )
        
        # Ligne de distance
        folium.PolyLine(
    locations=[p1, p2],
    color="orange" if dist_mode == "Vol d'oiseau" else "blue",
    weight=3,
    dash_array='10, 10'
).add_to(m)
        m.to_streamlit(height=600)

elif menu == "Focus Village":
    sel_village = st.selectbox("Choisir un village :", villages_df["Village"])
    v_data = infra_df[infra_df["Village"] == sel_village]
    
    st.header(f"Analyse de {sel_village}")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.table(v_data['Statut'].value_counts().reset_index())
    
    with c2:
        fig_pie = px.pie(v_data, names='Type', hole=0.5, title="Types d'infrastructures")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        fig_bar = px.bar(v_data['Statut'].value_counts().reset_index(), x='Statut', y='count', color='Statut',
                        color_discrete_map={"Réalisé": "#27ae60", "En cours": "#f1c40f", "Projeté": "#e74c3c"})
        st.plotly_chart(fig_bar, use_container_width=True)

elif menu == "Données RAW":
    st.header("Explorateur de données")
    st.dataframe(df_filtered, use_container_width=True)
    
    # Export Excel simple (CSV pour la démo)
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger les données", data=csv, file_name="sig_djinaky.csv", mime='text/csv')