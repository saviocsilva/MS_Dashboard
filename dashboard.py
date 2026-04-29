import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# URL da aba "Lançamentos" publicada como CSV
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTBb4_zoqS3pnWu2sV4_s-AzPLM_mykdPT7XfHJKywaWbdxDMSuUI1kzhmyLnqvTThQ-BMs_l8AnPQh/pub?gid=0&single=true&output=csv"
df = pd.read_csv(url)

# --- Tratamento da coluna Valor (moeda) ---
df['Valor'] = (
    df['Valor']
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)   # remove separador de milhar
    .str.replace(",", ".", regex=False)  # troca vírgula por ponto
)
df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')

# --- Tratamento da coluna Data ---
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')

# Coluna AnoMes em português manualmente
meses_pt = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}
df['AnoMes'] = df['Data'].dt.month.map(meses_pt) + "/" + df['Data'].dt.year.astype(str)

st.title("📊 Dashboard Financeiro")

# --- Indicadores principais ---
total_entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
total_saidas   = df[df['Tipo'] == 'Saída']['Valor'].sum()
saldo          = total_entradas - total_saidas

# Correção: usar "Pendente" em vez de "A Receber/A Pagar"
total_receber  = df[(df['Tipo'] == 'Entrada') & (df['Status'] == 'Pendente')]['Valor'].sum()
total_pagar    = df[(df['Tipo'] == 'Saída') & (df['Status'] == 'Pendente')]['Valor'].sum()

# Cards coloridos
def card(title, value, color):
    st.markdown(
        f"""
        <div style="background-color:{color};padding:20px;border-radius:10px;text-align:center">
            <h3 style="color:white;margin:0">{title}</h3>
            <h2 style="color:white;margin:0">R$ {value:,.2f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

col1, col2, col3 = st.columns(3)
with col1: card("💰 Total Entradas", total_entradas, "#2ecc71")
with col2: card("💸 Total Saídas", total_saidas, "#e74c3c")
with col3: card("📊 Saldo", saldo, "#3498db")

col4, col5 = st.columns(2)
with col4: card("📥 Total a Receber", total_receber, "#f1c40f")
with col5: card("📤 Total a Pagar", total_pagar, "#9b59b6")

# --- Gráfico de barras por mês ---
st.subheader("📊 Comparativo Mensal Entradas vs Saídas")
df_month = df.groupby(['AnoMes','Tipo'])['Valor'].sum().reset_index()
if not df_month.empty:
    fig_bar = px.bar(
        df_month,
        x='AnoMes',
        y='Valor',
        color='Tipo',
        barmode='group',
        text_auto=True,
        title="Entradas e Saídas por Mês"
    )
    fig_bar.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Gráfico de categorias ---
st.subheader("📌 Distribuição por Categoria")
if 'Categoria' in df.columns and not df['Categoria'].isnull().all():
    fig_cat = px.pie(df, values='Valor', names='Categoria',
                     title="Entradas e Saídas por Categoria")
    st.plotly_chart(fig_cat, use_container_width=True)

# --- Filtros interativos na tabela ---
st.subheader("🔎 Filtros Interativos na Tabela")
categorias = df['Categoria'].dropna().unique().tolist() if 'Categoria' in df.columns else []
status = df['Status'].dropna().unique().tolist() if 'Status' in df.columns else []
tipos = df['Tipo'].dropna().unique().tolist() if 'Tipo' in df.columns else []

cat_filter = st.multiselect("Filtrar por Categoria", categorias)
status_filter = st.multiselect("Filtrar por Status", status)
tipo_filter = st.multiselect("Filtrar por Tipo", tipos)
date_filter = st.date_input("Filtrar por período", [])

df_filtered = df.copy()
if cat_filter:
    df_filtered = df_filtered[df_filtered['Categoria'].isin(cat_filter)]
if status_filter:
    df_filtered = df_filtered[df_filtered['Status'].isin(status_filter)]
if tipo_filter:
    df_filtered = df_filtered[df_filtered['Tipo'].isin(tipo_filter)]
if date_filter:
    if len(date_filter) == 2:
        df_filtered = df_filtered[(df_filtered['Data'] >= pd.to_datetime(date_filter[0])) &
                                  (df_filtered['Data'] <= pd.to_datetime(date_filter[1]))]

st.dataframe(df_filtered)
