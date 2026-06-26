import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# Configuração da página
# --------------------------------------------------
st.set_page_config(
    page_title="Steam 2026 Dashboard",
    layout="wide",
    page_icon="🎮"
)

PALETTE  = px.colors.qualitative.Light24
TEMPLATE = "plotly_white"

# --------------------------------------------------
# Carregamento e pré-processamento dos dados
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("steam_games_2026.csv")
    df.columns = df.columns.str.rstrip(";").str.strip()

    for col in ["Price_USD", "Estimated_Owners", "Review_Score_Pct",
                "24h_Peak_Players", "Total_Reviews", "Discount_Pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Release_Date"] = pd.to_datetime(df["Release_Date"], errors="coerce")
    df["Release_Year"] = df["Release_Date"].dt.year.astype("Int64")

    # Preencher valores em falta para não perder jogos nos filtros
    df["Primary_Genre"] = df["Primary_Genre"].fillna("Outro")
    df["Release_Year"]  = df["Release_Year"].fillna(0).astype(int)

    def categorizar_preco(p):
        if p == 0:       return "F2P"
        elif p <= 10:    return "$0–$10"
        elif p <= 20:    return "$10–$20"
        elif p <= 40:    return "$20–$40"
        else:            return "$40–$70"

    df["Preco_Categoria"] = df["Price_USD"].apply(categorizar_preco)
    df["Revenue_Proxy"]   = df["Price_USD"] * df["Estimated_Owners"]
    df["Has_Multiplayer"] = df["All_Tags"].str.contains("Multiplayer", na=False).astype(int)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Ficheiro steam_games_2026.csv não encontrado na mesma pasta que este script.")
    st.stop()

CAT_ORDER = ["F2P", "$0–$10", "$10–$20", "$20–$40", "$40–$70"]
PAID_CAT  = ["$0–$10", "$10–$20", "$20–$40", "$40–$70"]

# --------------------------------------------------
# Sidebar — Filtros
# --------------------------------------------------
st.sidebar.header("Filtros")

years      = sorted(df["Release_Year"].dropna().unique().astype(int))
year_range = st.sidebar.slider("Ano de Lançamento",
                               min_value=int(min(years)),
                               max_value=int(max(years)),
                               value=(int(min(years)), int(max(years))))

sorted_genres = sorted(df["Primary_Genre"].dropna().unique())
genres        = st.sidebar.multiselect("Género Principal",
                                       options=sorted_genres,
                                       default=sorted_genres)

include_f2p = st.sidebar.checkbox("Incluir jogos F2P", value=True)

# Aplicar filtros
df_f = df[
    df["Release_Year"].between(year_range[0], year_range[1]) &
    df["Primary_Genre"].isin(genres)
].copy()

if not include_f2p:
    df_f = df_f[df_f["Preco_Categoria"] != "F2P"]

df_paid = df_f[df_f["Preco_Categoria"].isin(PAID_CAT)].copy()

if df_f.empty:
    st.warning("Nenhum dado para os filtros seleccionados.")
    st.stop()

# --------------------------------------------------
# Cabeçalho + KPIs
# --------------------------------------------------
st.title("🎮 Steam 2026 — Dashboard de Negócio")
st.markdown("Análise do mercado de videojogos PC &nbsp;·&nbsp; Estratégia de Preço Ideal")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🎮 Total de Jogos",          f"{len(df_f):,}", delta=f"{len(df_f) - len(df)} filtrados" if len(df_f) < len(df) else None)
c2.metric("💰 Jogos Pagos",              f"{len(df_paid):,}")
c3.metric("⭐ Review Score Médio",       f"{df_paid['Review_Score_Pct'].mean():.1f}%" if len(df_paid) else "—")
c4.metric("📈 Revenue Total Estimado",   f"${df_paid['Revenue_Proxy'].sum()/1e9:.1f}B" if len(df_paid) else "—")

st.divider()

# ══════════════════════════════════════════════════════════════
# SECÇÃO 1 — Evolução dos Jogos ao Longo dos Anos
# ══════════════════════════════════════════════════════════════
st.subheader("📅 1. Evolução dos Jogos ao Longo dos Anos")

# ── Gráfico principal: Nº de jogos por ano e género (largura total) ──
evo = (
    df_f
    .groupby(["Release_Year", "Primary_Genre"])
    .size()
    .reset_index(name="N_Jogos")
    .sort_values("Release_Year")
)
evo["Ano"] = evo["Release_Year"].astype(str)

fig1 = px.line(
    evo, x="Ano", y="N_Jogos", color="Primary_Genre",
    markers=True, template=TEMPLATE,
    color_discrete_sequence=PALETTE,
    title="Nº de Jogos Lançados por Ano e Género",
    labels={"N_Jogos": "Nº de Jogos", "Ano": "Ano", "Primary_Genre": "Género"},
)
fig1.update_layout(
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=-0.35,
                xanchor="center", x=0.5, title="",
                font=dict(size=12)),
    xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=12)),
    yaxis=dict(gridcolor="#ebebeb", tickfont=dict(size=12)),
    margin=dict(b=120),
    title_font=dict(size=16),
)
st.plotly_chart(fig1, use_container_width=True)

# ── Gráfico secundário: Revenue total por ano e género ──
rev_g = (
    df_paid
    .groupby(["Release_Year", "Primary_Genre"])["Revenue_Proxy"]
    .sum().reset_index()
    .sort_values("Release_Year")
)
rev_g["Ano"] = rev_g["Release_Year"].astype(str)
rev_g["Revenue (M USD)"] = (rev_g["Revenue_Proxy"] / 1e6).round(1)

fig2 = px.line(
    rev_g, x="Ano", y="Revenue (M USD)", color="Primary_Genre",
    markers=True, template=TEMPLATE,
    color_discrete_sequence=PALETTE,
    title="Revenue Total (M USD) por Ano e Género",
    labels={"Revenue (M USD)": "Revenue Total (M USD)", "Ano": "Ano", "Primary_Genre": "Género"},
)
fig2.update_layout(
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=-0.35,
                xanchor="center", x=0.5, title="",
                font=dict(size=12)),
    xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=12)),
    yaxis=dict(gridcolor="#ebebeb", tickfont=dict(size=12)),
    margin=dict(b=120),
    title_font=dict(size=16),
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# SECÇÃO 2 — Desempenho por Categoria de Preço e Género
# ══════════════════════════════════════════════════════════════
st.subheader("🏷️ 2. Desempenho por Categoria de Preço e Género")

cats_present = [c for c in PAID_CAT if c in df_paid["Preco_Categoria"].unique()]

col1_s2, col2_s2 = st.columns(2)

with col1_s2:
    rev_cat = (
        df_paid.groupby("Preco_Categoria")["Review_Score_Pct"]
        .mean().reindex(cats_present).round(1).reset_index()
    )
    rev_cat.columns = ["Categoria", "Review Score (%)"]

    fig3 = px.bar(
        rev_cat, x="Categoria", y="Review Score (%)",
        title="Review Score Médio por Categoria de Preço",
        text="Review Score (%)",
        color="Categoria",
        color_discrete_sequence=["#4C9BE8", "#3D7CC9", "#2E5DAB", "#1F3E8C"],
        template=TEMPLATE,
    )
    fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside", textfont_size=13)
    fig3.update_layout(showlegend=False, yaxis=dict(range=[0, 100], gridcolor="#ebebeb"))
    st.plotly_chart(fig3, use_container_width=True)

with col2_s2:
    rev_genre = (
        df_paid.groupby("Primary_Genre")["Review_Score_Pct"]
        .mean().sort_values(ascending=True).round(1).reset_index()
    )
    rev_genre.columns = ["Género", "Review Score (%)"]

    fig4 = px.bar(
        rev_genre, x="Review Score (%)", y="Género", orientation="h",
        title="Review Score Médio por Género",
        text="Review Score (%)",
        color="Review Score (%)",
        color_continuous_scale="Blues",
        template=TEMPLATE,
    )
    fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside", textfont_size=12)
    fig4.update_layout(coloraxis_showscale=False,
                       xaxis=dict(range=[0, 105], showgrid=False),
                       yaxis=dict(gridcolor="#ebebeb"))
    st.plotly_chart(fig4, use_container_width=True)

col3_s2, col4_s2 = st.columns(2)

with col3_s2:
    own_cat = (
        df_paid.groupby("Preco_Categoria")["Estimated_Owners"]
        .mean().reindex(cats_present).reset_index()
    )
    own_cat.columns = ["Categoria", "Owners Médios"]
    own_cat["Owners (M)"] = (own_cat["Owners Médios"] / 1e6).round(2)

    fig5 = px.bar(
        own_cat, x="Categoria", y="Owners (M)",
        title="Owners Médios por Categoria (Milhões)",
        text="Owners (M)",
        color="Categoria",
        color_discrete_sequence=["#52B788", "#40916C", "#2D6A4F", "#1B4332"],
        template=TEMPLATE,
    )
    fig5.update_traces(texttemplate="%{text:.2f}M", textposition="outside", textfont_size=13)
    fig5.update_layout(showlegend=False, yaxis=dict(gridcolor="#ebebeb"))
    st.plotly_chart(fig5, use_container_width=True)

with col4_s2:
    rev_by_genre = (
        df_paid.groupby("Primary_Genre")["Revenue_Proxy"]
        .sum().sort_values(ascending=True).reset_index()
    )
    rev_by_genre.columns = ["Género", "Revenue Total"]
    rev_by_genre["Revenue (B)"] = (rev_by_genre["Revenue Total"] / 1e9).round(2)

    fig6 = px.bar(
        rev_by_genre, x="Revenue (B)", y="Género", orientation="h",
        title="Revenue Total Estimado por Género (Mil M USD)",
        text="Revenue (B)",
        color="Revenue (B)",
        color_continuous_scale="Greens",
        template=TEMPLATE,
    )
    fig6.update_traces(texttemplate="$%{text:.2f}B", textposition="outside", textfont_size=12)
    fig6.update_layout(coloraxis_showscale=False,
                       xaxis=dict(showgrid=False),
                       yaxis=dict(gridcolor="#ebebeb"))
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("##### Tabela Resumo por Categoria de Preço")
summary = (
    df_paid.groupby("Preco_Categoria")
    .agg(
        N_Jogos         =("Name",             "count"),
        Preco_Medio_USD =("Price_USD",        "mean"),
        Review_Score_Med=("Review_Score_Pct", "mean"),
        Owners_Medio    =("Estimated_Owners", "mean"),
        Revenue_Medio   =("Revenue_Proxy",    "mean"),
        Pct_Multiplayer =("Has_Multiplayer",  "mean"),
    )
    .reindex(cats_present)
    .round(2)
)
st.dataframe(summary, use_container_width=True)

# --------------------------------------------------
# Rodapé
# --------------------------------------------------
st.caption("Dados: Steam API · Junho 2026 · Projeto Final — Análise de Dados")





































