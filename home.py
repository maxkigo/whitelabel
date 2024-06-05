import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.express as px


st.set_page_config(
    page_title="Kigo - Whitelabels",
    layout="wide"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.write()

with col2:
    st.image('https://main.d1jmfkauesmhyk.amplifyapp.com/img/logos/logos.png')

with col3:
    st.title('Kigo Analítica - Whitelabels')

with col4:
    st.write()

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

@st.cache_data()
def usos_withlabel(source):
    query_whitelabel = f"""
    SELECT P.parkingLotName AS proyecto,
       SUM(CASE WHEN QR.source = "kigo" THEN 1 ELSE 0 END) AS lecturas_kigo,
       SUM(CASE WHEN QR.source = "espacia" THEN 1 ELSE 0 END) AS lecturas_espacia,
       SUM(CASE WHEN QR.source = "bestparking" THEN 1 ELSE 0 END) AS lecturas_bestparking,
       SUM(CASE WHEN (QR.source != "kigo" AND QR.source != "espacia" AND QR.source != "bestparking") THEN 1 ELSE 0 END) AS lecturas_kigo_oldversion,
       COUNT(DISTINCT QR.id) AS lecturas_totales
    FROM `parkimovil-app`.cargomovil_pd.PKM_PARKING_LOT_GATE_CAT G
    INNER JOIN  `parkimovil-app`.cargomovil_pd.PKM_PARKING_LOT_CAT P
    ON G.parkingLotId = P.id
    INNER JOIN  `parkimovil-app`.cargomovil_pd.qr_user_read QR
    ON G.gateQrCode = QR.qr_code
    GROUP BY  P.parkingLotName
    HAVING SUM(CASE WHEN QR.source = '{source}' THEN 1 ELSE 0 END) > 0
    """

    df_whitelabel = client.query(query_whitelabel).to_dataframe()
    return df_whitelabel

source = ['kigo', 'bestparking', 'espacia']
source_seleccionada = st.selectbox('Selecciona una app:', source)

df_apps = usos_withlabel(source_seleccionada)


def time_whitelabel(proyecto):
    query_time = f"""
    SELECT EXTRACT(DATE FROM DATE_ADD(created, INTERVAL -6 HOUR)) AS fecha, 
    CASE 
        WHEN QR.source NOT IN ('kigo', 'espacia', 'bestparking') THEN 'kigo/old_version'
        ELSE QR.source
    END AS source, 
    COUNT(DISTINCT QR.id) AS lecturas,
    FROM `parkimovil-app`.cargomovil_pd.PKM_PARKING_LOT_GATE_CAT G
    INNER JOIN  `parkimovil-app`.cargomovil_pd.PKM_PARKING_LOT_CAT P
    ON G.parkingLotId = P.id
    INNER JOIN  `parkimovil-app`.cargomovil_pd.qr_user_read QR
    ON G.gateQrCode = QR.qr_code
    WHERE P.parkingLotName IN ({proyecto})
    GROUP BY  EXTRACT(DATE FROM DATE_ADD(created, INTERVAL -6 HOUR)), QR.source
    ORDER BY fecha
    """

    df_time_whitelabel = client.query(query_time).to_dataframe()
    return df_time_whitelabel

proyecto_list = df_apps['proyecto'].tolist()

proyectos_seleccionados = st.multiselect('Selecciona una proyecto:', proyecto_list)

if proyectos_seleccionados:
    proyectos_str = ', '.join(f"'{m}'" for m in proyectos_seleccionados)
    df_time = time_whitelabel(proyectos_str)
    fig = px.bar(df_time, x="fecha", y="lecturas", color='source')
    selected_apps_df = df_apps[df_apps['proyecto'].isin(proyectos_seleccionados)]
    percentage_kigo = (selected_apps_df['lecturas_kigo'].sum() * 100) / selected_apps_df['lecturas_totales'].sum()
    percentage_kigo_old = (selected_apps_df['lecturas_kigo_oldversion'].sum() * 100) / selected_apps_df['lecturas_totales'].sum()
    percentage_bestparking = (selected_apps_df['lecturas_bestparking'].sum() * 100) / selected_apps_df['lecturas_totales'].sum()
    percentage_espacia = (selected_apps_df['lecturas_espacia'].sum() * 100) / selected_apps_df['lecturas_totales'].sum()
    fig_kigo = go.Figure(go.Indicator(
        mode="number",
        value=percentage_kigo,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Kigo", 'font': {'color': "#F24405"}, 'align': 'center'}
    ))
    fig_kigold = go.Figure(go.Indicator(
        mode="number",
        value=percentage_kigo_old,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Kigo / Old Version", 'font': {'color': "#F24405"}, 'align': 'center'}
    ))
    fig_bestparking = go.Figure(go.Indicator(
        mode="number",
        value=percentage_bestparking,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Bestparking", 'font': {'color': "#F24405"}, 'align': 'center'}
    ))
    fig_espacia = go.Figure(go.Indicator(
        mode="number",
        value=percentage_espacia,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Espacia", 'font': {'color': "#F24405"}, 'align': 'center'}
    ))
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.plotly_chart(fig_kigo)
    with col6:
        st.plotly_chart(fig_kigold)
    with col7:
        st.plotly_chart(fig_bestparking)
    with col8:
        st.plotly_chart(fig_espacia)
    st.plotly_chart(fig, use_container_width=True)
st.write(df_apps)
