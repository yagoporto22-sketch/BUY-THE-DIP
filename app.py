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
            
           # --- NUEVA LÓGICA DE MAX DRAWDOWN 
            fin_ventana_dd = min(idx + 1008, len(precios))
            periodo_posterior = precios[idx:fin_ventana_dd]
            
            max_dd = ((np.min(periodo_posterior) - precios[idx]) / precios[idx]) * 100
            
            # Creamos la fila con los datos básicos
            fila = {
                'Fecha': fechas[idx].date(), 
                'Precio': round(float(precios[idx]), 2), 
                'Max DD %': round(float(max_dd), 2)
            }
            
            # Calculamos las rentabilidades a plazos fijos
            for n, d in [('1M', 21), ('3M', 63), ('6M', 126), ('12M', 252), ('24M', 504)]:
                if idx + d < len(df):
                    rent = ((df.iloc[idx + d]['Price'] - precios[idx]) / precios[idx]) * 100
                    fila[n] = round(float(rent), 2)
                else:
                    fila[n] = None # Si no ha pasado suficiente tiempo, ponemos vacío
            
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

# --- 5. TABLAS DE DETALLE Y MEDIAS (DISEÑO GOLD EDITION) ---
        st.subheader("📋 Detalle de Operaciones y Medias")
        
        # Preparamos el visual (índice empieza en 1)
        df_visual = df_res.copy()
        df_visual.index = df_visual.index + 1

        # FUNCIÓN ÚNICA CORREGIDA
        def style_rentabilidad(val):
            try:
                v = float(val)
                if v < -20:
                    return 'background-color: #ffcccc; color: #990000' # Rojo
                elif v > 50:
                    # Fondo Oro, Letra Negra, Negrita (Legible y Pro)
                    return 'background-color: #c8b273; color: #FFD700'
                elif v > 20:
                    return 'background-color: #c6efce; color: #006100' # Verde
                return ''
            except:
                return ''

        cols_interes = ['1M', '3M', '6M', '12M', '24M']
        cols_actuales = [c for c in cols_interes if c in df_visual.columns]
        
        # Aplicamos el estilo
        df_styled = df_visual.style.map(style_rentabilidad, subset=cols_actuales)

        # MOSTRAR TABLAS
        col1, col2 = st.columns([2, 1])
        with col1: 
            st.dataframe(df_styled, use_container_width=True)
        with col2: 
            st.table(df_res[cols_actuales].mean().to_frame(name="Media %"))

        # --- 6. BALANCE DE ESTRATEGIA (WIN RATE) ---
        st.subheader("🏆 Probabilidad de Éxito (Win Rate)")
        stats = []

        for col in cols_interes:
            if col in df_res.columns:
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
            st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

        # --- 6. BALANCE DE ESTRATEGIA (WIN RATE) ---
        st.subheader("🏆 Probabilidad de Éxito (Win Rate)")
        stats = []

        for col in cols_interes:
            if col in df_res.columns:
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
            st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

        # --- 6. BALANCE DE ESTRATEGIA (WIN RATE) ---
        st.subheader("🏆 Probabilidad de Éxito (Win Rate)")
        stats = []

        for col in cols_interes:
            if col in df_res.columns:
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
            st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)
    
