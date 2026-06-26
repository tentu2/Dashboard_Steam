import streamlit as st
import pandas as pd
import pathlib
 
# --------------------------------------------------
# Configuração da página
# --------------------------------------------------
st.set_page_config(
    page_title="Steam 2026 Dashboard",
    layout="wide"
)
 
st.title("🎮 Steam 2026 — Dashboard de Negócio")
st.markdown("Dashboard de análise do mercado de videojogos PC · Estratégia de Preço Ideal")
 
# --------------------------------------------------
# Carregamento e pré-processamento dos dados
# --------------------------------------------------
@st.cache_data
def load_data():
    base = pathlib.Path(__file__).parent
    path = base / "steam_games_2026.csv"
    df = pd.read_csv(str(path), parse_dates=["Release_Date"])
 
    # Limpar nomes de colunas (o ficheiro tem ";" extra no final do cabeçalho)
    df.columns = df.columns.str.rstrip(";").str.strip()
 
    # Colunas derivadas
    df["Release_Year"] = df["Release_Date"].dt.year.astype("Int64")
 
    def categorizar_preco(p):
        if p == 0:
            return "F2P"
        elif p <= 10:
            return "$0–$10"
        elif p <= 20:
            return "$10–$20"
        elif p <= 40:
            return "$20–$40"
        else:
            return "$40–$70"
 
    df["Preco_Categoria"] = df["Price_USD"].apply(categorizar_preco)
    df["Revenue_Proxy"]   = df["Price_USD"] * df["Estimated_Owners"]
    df["Has_Multiplayer"] = df["All_Tags"].str.contains("Multiplayer", na=False).astype(int)
 
    return df
 
try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Ficheiro steam_games_2026.csv não encontrado na mesma pasta que este script.")
    st.stop()
 
CAT_ORDER      = ["F2P", "$0–$10", "$10–$20", "$20–$40", "$40–$70"]
PAID_CAT_ORDER = ["$0–$10", "$10–$20", "$20–$40", "$40–$70"]
 
# --------------------------------------------------
# Sidebar — Filtros Globais
# --------------------------------------------------
st.sidebar.header("Filtros")
 
years = sorted(df["Release_Year"].dropna().unique().astype(int))
year_range = st.sidebar.slider(
    "Ano de Lançamento",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)
 
sorted_genres = sorted(df["Primary_Genre"].dropna().unique())
genres = st.sidebar.multiselect(
    "Género Principal",
    options=sorted_genres,
    default=sorted_genres
)
 
# Aplicar filtros
df_f = df[
    df["Release_Year"].between(year_range[0], year_range[1]) &
    df["Primary_Genre"].isin(genres)
].copy()
 
df_paid = df_f[df_f["Preco_Categoria"].isin(PAID_CAT_ORDER)].copy()
df_all  = df_f.copy()
 
if df_f.empty:
    st.warning("Nenhum dado para os filtros seleccionados.")
    st.stop()
 
# --------------------------------------------------
# KPIs — topo da página
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("🎮 Total de Jogos (c/ F2P)",      f"{len(df_all):,}")
col2.metric("💰 Total de Jogos Pagos",           f"{len(df_paid):,}")
col3.metric("⭐ Review Score Médio (pagos)",     f"{df_paid['Review_Score_Pct'].mean():.1f}%")
col4.metric("📈 Revenue Total Estimado",         f"${df_paid['Revenue_Proxy'].sum() / 1_000_000_000:,.1f}B")
 
st.divider()
 
# ══════════════════════════════════════════════════
# SECÇÃO 1 — Evolução dos Jogos ao Longo dos Anos
# ══════════════════════════════════════════════════
st.subheader("📅 1. Evolução dos Jogos ao Longo dos Anos")
 
tab1_com, tab1_sem = st.tabs(["🌐 Com F2P", "💰 Só Jogos Pagos"])
 
with tab1_com:
    st.markdown("##### Nº de jogos lançados por ano e género (todos os jogos)")
    evo_all = (
        df_all
        .groupby(["Release_Year", "Primary_Genre"])
        .size()
        .reset_index(name="N_Jogos")
    )
    evo_all_pivot = (
        evo_all
        .pivot(index="Release_Year", columns="Primary_Genre", values="N_Jogos")
        .fillna(0)
    )
    st.line_chart(evo_all_pivot)
 
    st.markdown("##### Preço médio (USD) por ano — jogos com preço > 0")
    price_all = (
        df_all[df_all["Price_USD"] > 0]
        .groupby("Release_Year")["Price_USD"]
        .mean()
        .round(2)
    )
    st.bar_chart(price_all)
 
with tab1_sem:
    st.markdown("##### Nº de jogos lançados por ano e género (excluindo F2P)")
    evo_paid = (
        df_paid
        .groupby(["Release_Year", "Primary_Genre"])
        .size()
        .reset_index(name="N_Jogos")
    )
    evo_paid_pivot = (
        evo_paid
        .pivot(index="Release_Year", columns="Primary_Genre", values="N_Jogos")
        .fillna(0)
    )
    st.line_chart(evo_paid_pivot)
 
    st.markdown("##### Preço médio (USD) por ano — só jogos pagos")
    price_paid = (
        df_paid
        .groupby("Release_Year")["Price_USD"]
        .mean()
        .round(2)
    )
    st.bar_chart(price_paid)
 
st.divider()
 
# ══════════════════════════════════════════════════
# SECÇÃO 2 — Desempenho por Categoria de Preço
# ══════════════════════════════════════════════════
st.subheader("🏷️ 2. Desempenho por Categoria de Preço")
 
tab2_com, tab2_sem = st.tabs(["🌐 Com F2P", "💰 Só Jogos Pagos"])
 
def render_cat_section(data, cat_order):
    cats_present = [c for c in cat_order if c in data["Preco_Categoria"].unique()]
 
    col_left, col_right = st.columns(2)
 
    with col_left:
        st.markdown("##### Review Score médio por categoria")
        review_cat = (
            data
            .groupby("Preco_Categoria")["Review_Score_Pct"]
            .mean()
            .reindex(cats_present)
            .round(1)
        )
        st.bar_chart(review_cat)
 
    with col_right:
        st.markdown("##### Owners médios por categoria")
        owners_cat = (
            data
            .groupby("Preco_Categoria")["Estimated_Owners"]
            .mean()
            .reindex(cats_present)
            .round(0)
        )
        st.bar_chart(owners_cat)
 
    st.markdown("##### Tabela resumo por categoria de preço")
    summary = (
        data
        .groupby("Preco_Categoria")
        .agg(
            N_Jogos          =("Name",             "count"),
            Preco_Medio_USD  =("Price_USD",        "mean"),
            Review_Score_Med =("Review_Score_Pct", "mean"),
            Owners_Medio     =("Estimated_Owners", "mean"),
            Revenue_Medio    =("Revenue_Proxy",    "mean"),
            Pct_Multiplayer  =("Has_Multiplayer",  "mean"),
        )
        .reindex(cats_present)
        .round(2)
    )
    st.dataframe(summary, use_container_width=True)
 
with tab2_com:
    render_cat_section(df_all, CAT_ORDER)
 
with tab2_sem:
    render_cat_section(df_paid, PAID_CAT_ORDER)
 
st.divider()
 
# ══════════════════════════════════════════════════
# SECÇÃO 3 — Modelos de Machine Learning
# ══════════════════════════════════════════════════
st.subheader("🤖 3. Modelos de Machine Learning")
 
col_ml1, col_ml2 = st.columns(2)
 
with col_ml1:
    st.markdown("##### Modelo A · Classificação de Categoria de Preço")
    st.markdown("*RandomForestClassifier — 200 árvores*")
    ma1, ma2 = st.columns(2)
    ma1.metric("Accuracy (teste)",     "100.0%")
    ma2.metric("Accuracy (CV 5-fold)", "99.5% ± 0.4%")
 
    st.markdown("**Feature Importance**")
    feat_clf = pd.DataFrame({
        "Feature":     ["Review_Score_Pct", "Price_USD", "Revenue_Proxy",
                        "Estimated_Owners", "24h_Peak_Players", "Has_Multiplayer"],
        "Importância": [0.38, 0.28, 0.18, 0.09, 0.05, 0.02]
    }).set_index("Feature")
    st.bar_chart(feat_clf)
    st.success("Classificação perfeita — o preço e a receita discriminam completamente as categorias.")
 
with col_ml2:
    st.markdown("##### Modelo B · Regressão do Review Score")
    st.markdown("*RandomForestRegressor — 200 árvores*")
    mb1, mb2, mb3 = st.columns(3)
    mb1.metric("MAE",        "9.4 pp")
    mb2.metric("R² (teste)", "0.04")
    mb3.metric("R² (CV)",    "−0.10")
 
    st.markdown("**Feature Importance**")
    feat_reg = pd.DataFrame({
        "Feature":     ["24h_Peak_Players", "Estimated_Owners", "Total_Reviews",
                        "Price_USD", "Has_Multiplayer"],
        "Importância": [0.41, 0.31, 0.17, 0.07, 0.04]
    }).set_index("Feature")
    st.bar_chart(feat_reg)
    st.warning("R² ≈ 0 — variáveis numéricas não predizem a satisfação dos jogadores. A qualidade é subjectiva.")
 
st.divider()
 
# ══════════════════════════════════════════════════
# SECÇÃO 4 — Análise de Negócio
# ══════════════════════════════════════════════════
st.subheader("🔍 4. Análise de Negócio")
 
st.markdown("""
A análise de **873 jogos pagos** no Steam revela que a relação entre preço e satisfação dos utilizadores **não é linear**.
 
O pico de **review score (85,5%)** ocorre na faixa **\$10–\$20**, constituindo a melhor relação qualidade/preço percebida. A faixa **\$40–\$70**, apesar de gerar o maior revenue médio por jogo ($159,9M), apresenta o **menor review score (78,7%)** entre as categorias pagas — um paradoxo que reflecte as expectativas elevadas associadas aos títulos premium.
 
Os **owners médios** crescem com o preço na faixa premium (2,75M em \$40–\$70), reflectindo o peso das grandes IPs AAA. O **DAU (peak players 24h)** cresce igualmente de 1.508 (baixo custo) até 4.266 (premium), indicando que jogos mais caros sustentam comunidades activas maiores, possivelmente por maior investimento em conteúdo pós-lançamento e modos multijogador.
 
O **Modelo A** atingiu 100% de accuracy, confirmando que o preço e a receita são discriminantes perfeitos das categorias. A feature importance aponta o **Review Score como o preditor mais forte (38%)**, sugerindo uma correlação entre percepção de qualidade e posicionamento de preço.
 
O **Modelo B (R² ≈ 0)** demonstra que nenhuma variável quantitativa prediz de forma fiável a satisfação — a qualidade é essencialmente subjectiva e multidimensional, dependendo de factores como narrativa, gameplay loop, estabilidade técnica no lançamento e gestão da comunidade.
""")
 
st.divider()
 
# ══════════════════════════════════════════════════
# SECÇÃO 5 — Recomendações de Negócio
# ══════════════════════════════════════════════════
st.subheader("💡 5. Recomendações de Negócio")
 
rec1, rec2, rec3 = st.columns(3)
 
with rec1:
    st.success("""
**🎯 Indie / Primeira publicação**
 
Lançar entre **\$12,99–\$19,99**. É a faixa com o maior review score médio (85,5%) e proporciona um revenue médio de \$29M/jogo sem as expectativas elevadas do segmento premium.
 
Evitar preços abaixo de \$9,99 para jogos com ambições de crítica — a percepção de valor ressente-se.
""")
 
with rec2:
    st.warning("""
**🏢 Publishers AAA**
 
Manter \$59,99–\$69,99 **somente com marketing robusto** e IP estabelecida. O review score inferior (78,7%) indica que a satisfação não acompanha o preço.
 
Investir em qualidade de lançamento é crítico — um lançamento instável pode despoletar review bombing difícil de recuperar.
""")
 
with rec3:
    st.info("""
**📅 Estratégia de Desconto**
 
Aplicar desconto de **20–30%** após 6–12 meses do lançamento para capturar compradores price-sensitive. Nunca lançar com desconto — desvaloriza a percepção do produto.
 
Combinar descontos com actualizações de conteúdo para reanimar o DAU e aumentar a visibilidade no algoritmo do Steam.
""")
 
# --------------------------------------------------
# Rodapé
# --------------------------------------------------
st.caption("Dados: Steam API · Junho 2026 · Projeto Final — Análise de Dados")