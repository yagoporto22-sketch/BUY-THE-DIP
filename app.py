import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go # <--- NUEVA LIBRERÍA PARA GRÁFICOS PRO
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Yago Strategic Advisor", layout="wide")
st.title("📊 Analizador Buy The Dip")

# BARRA LATERAL
st.sidebar.header("⚙️ Parámetros de Estrategia")
ticker = st.sidebar.text_input("Ticker", value="MSFT").upper()
caida_obj = st.sidebar.slider("% Caída desde ATH", 5, 80, 35)
years = st.sidebar.slider("Años de Historial", 1, 50, 30)

if st.sidebar.button("🚀 Ejecutar Análisis"):
    # 2. MOTOR DE DATOS (Tu código)
    fecha_inicio = (datetime.now() - timedelta(days=years * 365)).strftime('%Y-%m-%d')
    df = yf.download(ticker, start=fecha_inicio)
    
    if df.empty:
        st.error("No hay datos para este Ticker.")
    else:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[['Close']].copy()
        df.rename(columns={'Close': 'Price'}, inplace=True)

        # Lógica de señales
        precios = df['Price'].values
        fechas = df.index
        señales_indices = []
        ultimo_ath = precios[0]
        objetivo = 1 - (caida_obj / 100)

        for i in range(1, len(precios)):
            if precios[i] > ultimo_ath: ultimo_ath = precios[i]
            if precios[i] <= (ultimo_ath * objetivo):
                señales_indices.append(i)
                ultimo_ath = precios[i]

        # 3. PROCESAMIENTO
        resultados = []
        for k, idx in enumerate(señales_indices):
            # ... (Toda tu lógica de Max DD y plazos de 1, 3, 6, 12 meses)
            # [Para ahorrar espacio asumo que mantienes tu bloque de procesamiento aquí]
            # [Asegúrate de que la lista 'resultados' se llene como en tu código anterior]
            
            # --- (Inserta aquí tu bucle de resultados que ya tenías) ---
            siguiente_limite = señales_indices[k+1] if k+1 < len(señales_indices) else len(precios)
            periodo_posterior = precios[idx:siguiente_limite]
            max_dd = ((np.min(periodo_posterior) - precios[idx]) / precios[idx]) * 100
            fila = {'Fecha': fechas[idx].date(), 'Precio': round(float(precios[idx]), 2), 'Max DD %': round(float(max_dd), 2)}
            for n, d in [('1M', 21), ('3M', 63), ('6M', 126), ('12M', 252), ('24M', 504)]:
                if idx + d < len(df):
                    rent = ((df.iloc[idx + d]['Price'] - precios[idx]) / precios[idx]) * 100
                    fila[n] = round(float(rent), 2)
            resultados.append(fila)

        df_res = pd.DataFrame(resultados)

        # 4. MEJORA VISUAL: EL GRÁFICO INTERACTIVO
        st.subheader(f"📈 Gráfico Histórico de {ticker}")
        fig = go.Figure()
        # Línea de precio
        fig.add_trace(go.Scatter(x=df.index, y=df['Price'], name='Precio', line=dict(color='#1f77b4', width=1.5)))
        # Puntos de compra
        if not df_res.empty:
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df_res['Fecha']), 
                y=df_res['Precio'], 
                mode='markers', 
                name='Puntos de Compra',
                marker=dict(color='#2ca02c', size=10, symbol='triangle-up', line=dict(width=2, color="white"))
            ))
        
        fig.update_layout(hovermode="x unified", template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # 5. TABLAS (Tus tablas de siempre)
        st.subheader("📋 Detalle de Operaciones y Medias")
        col1, col2 = st.columns([2, 1])
        with col1: 
    # CREAMOS UNA COPIA PARA NO ROMPER EL ORIGINAL
    df_visual = df_res.copy()
    
    # CAMBIAMOS EL ÍNDICE: LE SUMAMOS 1 A CADA NÚMERO
    df_visual.index = df_visual.index + 1
    
    # MOSTRAMOS LA TABLA YA MODIFICADA
    st.dataframe(df_visual, use_container_width=True)

with col2: 
    # La tabla de medias no tiene índice numérico (usa los plazos), 
    # así que esta se queda igual de bien.
    st.table(df_res[['1M', '3M', '6M', '12M', '24M']].mean().to_frame(name="Media %"))
     
        # --- 6. BALANCE DE ESTRATEGIA (GANADAS VS PERDIDAS) ---
st.subheader("🏆 Probabilidad de Éxito (Win Rate)")
stats = []

# Analizamos cada columna de plazo
for col in ['1M', '3M', '6M', '12M', '24M']:
    # Solo contamos las que tienen datos (filtramos los N/A)
    datos_validos = df_res[col].dropna()
    total = len(datos_validos)
    
    if total > 0:
        ganadas = (datos_validos > 0).sum()
        perdidas = (datos_validos <= 0).sum()
        win_rate = (ganadas / total) * 100
        
        stats.append({
            'Plazo': col,
            'Total Ops': total,
            'Ganadas ✅': int(ganadas),
            'Perdidas ❌': int(perdidas),
            'Win Rate (%)': f"{round(win_rate, 2)}%"
        })

if stats:
    df_stats = pd.DataFrame(stats)
    # Mostramos la tabla centrada y ocupando el ancho
    st.dataframe(df_stats, use_container_width=True, hide_index=True)
else:
    st.info("No hay suficientes datos históricos para calcular el balance.")
