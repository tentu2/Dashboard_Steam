import streamlit as st
import pandas as pd
import os

# --------------------------------------------------
# Configuração da página
# --------------------------------------------------
st.set_page_config(
    page_title="Steam 2026 Dashboard",  # O título que mostra na tab do browser
    layout="wide"                        # A opção "centered" coloca a página numa coluna central
)

st.title("🎮 Steam 2026 — Dashboard de Negócio")
st.markdown("Dashboard de análise do mercado de videojogos PC · Estratégia de Preço Ideal")

# --------------------------------------------------
# Carregamento dos dados
# --------------------------------------------------
# Esta linha é extremamente importante.
# Ao ler o ficheiro a primeira vez, a app guarda os dados em memória (cache)
# Assim, sempre que houver interações com o dashboard (ex: mudar um filtro), não é necessário ler o ficheiro csv novamente
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(base, "Projeto_Final_Terminado", "data", "processed", "steam_clean.csv")
    df = pd.read_csv(file_name, parse_dates=["Release_Date"])
    # Excluir jogos F2P e sem revenue para análise de preço
    df = df[(df["Revenue_Proxy"] > 0) & (df["Preco_Categoria"] != "F2P")]
    return df

df = load_data()

# --------------------------------------------------
# Definir um Sidebar com filtros
# --------------------------------------------------
st.sidebar.header("Filtros")

# Filtro de Categoria de Preço
cat_order = ["$0–$10", "$10–$20", "$20–$40", "$40–$70"]
available_cats = [c for c in cat_order if c in df["Preco_Categoria"].unique()]
categories = st.sidebar.multiselect(
    "Categoria de Preço",
    options=available_cats,
    default=available_cats
)

# Filtro de Género
sorted_genres = sorted(df["Primary_Genre"].dropna().unique())
genres = st.sidebar.multiselect(
    "Género Principal",
    options=sorted_genres,
    default=sorted_genres
)

# Filtro de Ano
years = sorted(df["Release_Date"].dt.year.dropna().unique())
year_range = st.sidebar.slider(
    "Ano de Lançamento",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

# Aplicar filtros
filtered_df = df[
    (df["Preco_Categoria"].isin(categories)) &
    (df["Primary_Genre"].isin(genres)) &
    (df["Release_Date"].dt.year.between(year_range[0], year_range[1]))
]

# --------------------------------------------------
# Parte superior com KPIs
# --------------------------------------------------
total_revenue = filtered_df["Revenue_Proxy"].sum()
avg_review    = filtered_df["Review_Score_Pct"].mean()
num_games     = len(filtered_df)
avg_owners    = filtered_df["Estimated_Owners"].mean()

# Vamos dividir a área em 4 colunas para mostrar os KPIs lado a lado
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Revenue Total Estimado", f"${total_revenue / 1_000_000:,.1f}M")
col2.metric("⭐ Review Score Médio",      f"{avg_review:.1f}%")
col3.metric("🎮 Nº de Jogos",             num_games)
col4.metric("👥 Owners Médios",           f"{avg_owners / 1_000_000:.1f}M")

st.divider()

# ------------------------------------------------------------------
# Gráfico 1 - Revenue ao longo do tempo (cada categoria é uma série)
# ------------------------------------------------------------------
st.subheader("📅 Revenue ao longo do tempo por categoria de preço")

# Agrupar a soma de Revenue_Proxy em cada ano por Preco_Categoria
revenue_over_time = (
    filtered_df
    .groupby(
        [pd.Grouper(key="Release_Date", freq="YE"), "Preco_Categoria"]
    )["Revenue_Proxy"]
    .sum()
    .reset_index()
)

# Criar uma pivot table
revenue_pivot = revenue_over_time.pivot(
    index="Release_Date",
    columns="Preco_Categoria",
    values="Revenue_Proxy"
)

# Manter a ordem das categorias
cols_present = [c for c in cat_order if c in revenue_pivot.columns]
revenue_pivot = revenue_pivot[cols_present]

st.line_chart(revenue_pivot)

# --------------------------------------------------
# Gráfico 2 - Revenue por Género
# --------------------------------------------------
st.subheader("🕹️ Revenue total por género")

# Agrupar a soma de Revenue_Proxy por Primary_Genre
revenue_by_genre = (
    filtered_df
    .groupby("Primary_Genre")["Revenue_Proxy"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(revenue_by_genre)

# --------------------------------------------------
# Gráfico 3 - Review Score por Categoria de Preço
# --------------------------------------------------
st.subheader("⭐ Review Score médio por categoria de preço")

# Agrupar a média de Review_Score_Pct por Preco_Categoria
review_by_cat = (
    filtered_df[filtered_df["Preco_Categoria"].isin(cols_present)]
    .groupby("Preco_Categoria")["Review_Score_Pct"]
    .mean()
    .reindex(cols_present)
)

st.bar_chart(review_by_cat)

st.divider()

# --------------------------------------------------
# Table - Top 10 jogos por revenue
# --------------------------------------------------
st.subheader("🏆 Top 10 jogos por revenue estimado")

# Agrupar a soma de Revenue_Proxy por Name, ordenar e mostrar os top 10
top_games = (
    filtered_df
    .sort_values("Revenue_Proxy", ascending=False)
    .head(10)
    [["Name", "Preco_Categoria", "Price_USD", "Review_Score_Pct", "Estimated_Owners", "Revenue_Proxy"]]
    .rename(columns={
        "Name":               "Jogo",
        "Preco_Categoria":    "Categoria",
        "Price_USD":          "Preço ($)",
        "Review_Score_Pct":   "Review Score (%)",
        "Estimated_Owners":   "Owners Estimados",
        "Revenue_Proxy":      "Revenue Estimado ($)",
    })
    .reset_index(drop=True)
)

st.dataframe(top_games, use_container_width=True)

# --------------------------------------------------
# Rodapé
# --------------------------------------------------
st.caption("Dados: Steam API · Junho 2026 · Projeto Final — Análise de Dados")
