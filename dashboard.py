import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from dateutil.relativedelta import relativedelta
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, getcontext
getcontext().prec = 4

# Caminho para o arquivo de configurações
CONFIG_PATH = "data/settings.json"
CSV_PATH = "data/planilha_apostas.csv"

# Interface do Streamlit
st.set_page_config(page_title="Dashboard de Apostas", layout="wide")
st.title("📊 Dashboard de Apostas")

# Funções para carregar e salvar configurações
@st.cache_resource
def carregar_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "UNIDADE_APOSTA": 10,
            "BOOKIES": [],
            "SPORTS": [],
            "BET_TYPES": [],
            "CAPPERS": [],
            "COMPETITIONS": []
        }

def salvar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def salvar_dados(df):
    df.to_csv(CSV_PATH, index=False)

# Carrega as configurações
config = carregar_config()
BOOKIES = config.get("BOOKIES", [])
SPORTS = config.get("SPORTS", [])
BET_TYPES = config.get("BET_TYPES", [])
CAPPERS = config.get("CAPPERS", [])
COMPETITIONS = config.get("COMPETITIONS", [])
UNIDADE_APOSTA = config.get("UNIDADE_APOSTA", 10)

# Valor padrão se não estiver definido
if not isinstance(UNIDADE_APOSTA, (int, float)):
    UNIDADE_APOSTA = 10

# Salvar dados apostas
def carregar_dados():
    try:
        df = pd.read_csv("data/planilha_apostas.csv", parse_dates=["date"])
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "parlay", "bookie", "sport", "selection", "bet_type", "capper",
                                     "competition", "event", "extra_info", "live", "score", "units", "odd",
                                     "free_bet", "result", "lucro_unidade", "lucro_monetario", "unidade_vigente"])

def salvar_dados(df):
    df.to_csv("data/planilha_apostas.csv", index=False)

aba = st.sidebar.radio("Escolha uma aba", ["Dashboard", "Inserir Aposta", "Visualizar Apostas", "Configurações"])

# Removido o uso direto da variável dados aqui para recarregar após inserção
if aba != "Inserir Aposta":
    dados = carregar_dados()

if aba == "Inserir Aposta":
    st.subheader("➕ Inserir Nova Aposta")

    with st.form("form_inserir"):
        col1, col2, col3 = st.columns(3)

        with col1:
            data = st.date_input("Data", value=datetime.today())
            bookie = st.selectbox("Bookie", options=[""] + BOOKIES, index=0)
            sport = st.selectbox("Esporte", options=[""] + SPORTS, index=0)

        with col2:
            bet_type = st.selectbox("Tipo de Aposta", options=[""] + BET_TYPES, index=0)
            capper = st.selectbox("Capper", options=[""] + CAPPERS, index=0)
            competition = st.selectbox("Competição", options=[""] + COMPETITIONS, index=0)

        with col3:
            selection = st.text_input("Seleção")
            extra_info = st.text_input("Informações Extras")
            event = st.text_input("Evento")
            score = st.text_input("Placar", placeholder="")

        col4, col5, col6 = st.columns(3)
        with col4:
            parlay = st.radio("Parlay Leg", ["N", "S"], horizontal=True)

        with col5:
            live = st.radio("Live", ["N", "S"], horizontal=True)

        with col6:
            free_bet = st.radio("Free bet", ["N", "S"], horizontal=True)

        col7, col8 = st.columns(2)
        with col7:
            units = st.number_input("Valor Apostado (Unidades)", min_value=0.0, step=0.25)
        with col8:
            odd = st.number_input("Odd", min_value=1.0, step=0.01)

        result = st.selectbox("Resultado", ["W", "L", "R", "Em Aberto"])

        submitted = st.form_submit_button("Salvar Aposta")

        if submitted:
            lucro_unidade = units * odd - units if result == "W" else -units if result == "L" else 0
            lucro_monetario = lucro_unidade * UNIDADE_APOSTA

            if parlay == "S":
                units = None
                odd = None
                lucro_unidade = None
                lucro_monetario = None
                if result == "W":
                    result = "w"
                elif result ==  "L":
                    result = "l"
                elif result == "R":
                    result = "r"
            else:
                lucro_unidade = units * odd - units if result == "W" else -units if result == "L" else 0
                lucro_monetario = lucro_unidade * UNIDADE_APOSTA

            nova_linha_principal = {
                "date": data,
                "parlay": parlay,
                "bookie": bookie,
                "sport": sport,
                "selection": selection, 
                "bet_type": bet_type,
                "capper": capper,
                "competition": competition,
                "event": event,
                "extra_info": extra_info,
                "live": live,
                "score": score,
                "units": units,
                "odd": odd,
                "free_bet": free_bet,
                "result": result,
                "lucro_unidade": lucro_unidade,
                "lucro_monetario": lucro_monetario,
                "unidade_vigente": UNIDADE_APOSTA,
            }

            # Recarrega os dados do CSV, adiciona a aposta principal e salva
            dados = carregar_dados()
            dados = pd.concat([dados, pd.DataFrame([nova_linha_principal])], ignore_index=True)

            # Salva todos os dados no CSV
            salvar_dados(dados)

            st.success("✅ Aposta adicionada com sucesso!")

elif aba == "Visualizar Apostas":
    st.subheader("📄 Apostas Registradas")

    # Mostrar tabela completa
    st.dataframe(dados.iloc[::-1].reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    st.subheader("✏️ Editar Apostas Em Aberto")

    # Filtrar apenas apostas "Em Aberto"
    dados_em_aberto = dados[dados["result"] == "Em Aberto"]

    if dados_em_aberto.empty:
        st.info("Nenhuma aposta em aberto para editar.")
    else:
        opcoes = {
            f"({row['date']}) [{row['bookie']}] {row['selection']} - {row['bet_type']} - {row['event']} @ {row['odd']}": i
            for i, row in dados_em_aberto.iterrows()
        }

        opcao_escolhida = st.selectbox("Selecione a aposta", list(opcoes.keys()))
        index_aposta = opcoes[opcao_escolhida]

        aposta_editar = dados.loc[index_aposta].copy()
        aposta_editar.fillna("", inplace=True)

        with st.form("form_editar_resultado"):
            result = st.selectbox("Resultado", ["W", "L", "R"], index=0)
            score = st.text_input("Placar", value=aposta_editar["score"], placeholder="")
            submitted = st.form_submit_button("Atualizar")

            if submitted:
                # Calcular lucro com base no novo resultado
                if aposta_editar["parlay"] == "S":
                    lucro_unidade = None
                    lucro_monetario = None
                    result = result.lower()
                else:
                    units = float(aposta_editar["units"])
                    odd = float(aposta_editar["odd"])
                    lucro_unidade = units * odd - units if result == "W" else -units if result == "L" else 0
                    lucro_monetario = lucro_unidade * float(aposta_editar["unidade_vigente"])

                # Atualizar os dados
                dados.at[index_aposta, "score"] = score
                dados.at[index_aposta, "result"] = result
                dados.at[index_aposta, "lucro_unidade"] = lucro_unidade
                dados.at[index_aposta, "lucro_monetario"] = lucro_monetario

                salvar_dados(dados)
                st.success("✅ Resultado atualizado com sucesso!")


if aba == "Dashboard":
    st.subheader("📈 Análise das Apostas")

    with st.sidebar:
        st.markdown("### Filtros")
        data_inicio = pd.to_datetime(st.date_input("Data Início", value=dados["date"].min() if not dados.empty else datetime.today())).date()
        data_fim = pd.to_datetime(st.date_input("Data Fim", value=dados["date"].max() if not dados.empty else datetime.today())).date()
        bookie_filtro = st.multiselect("Bookie", options=dados["bookie"].unique())
        sport_filtro = st.multiselect("Esporte", options=dados["sport"].unique())
        bet_type_filtro = st.multiselect("Tipo de Aposta", options=dados["bet_type"].unique())
        capper_filtro = st.multiselect("Capper", options=dados["capper"].unique())
        competition_filtro = st.multiselect("Competição", options=dados["competition"].unique())

    dados_filtrados = dados.copy()
    dados_filtrados["date"] = pd.to_datetime(dados_filtrados["date"]).dt.date
    dados_filtrados = dados_filtrados[
        (dados_filtrados["date"] >= data_inicio) &
        (dados_filtrados["date"] <= data_fim)
    ]

    if bookie_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados["bookie"].isin(bookie_filtro)]
    if sport_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados["sport"].isin(sport_filtro)]
    if bet_type_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados["bet_type"].isin(bet_type_filtro)]
    if capper_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados["capper"].isin(capper_filtro)]
    if competition_filtro:
        dados_filtrados = dados_filtrados[dados_filtrados["competition"].isin(competition_filtro)]

    total_unidades_apostadas = dados_filtrados[
        (dados_filtrados["parlay"] == "N") & 
        (dados_filtrados["units"].notnull())
    ]["units"].sum()

    dados_filtrados["lucro_unidade"] = dados_filtrados.apply(lambda row:
        float(Decimal(row["units"]) * Decimal(row["odd"]) - Decimal(row["units"])) if row["result"] == "W" else
        float(-Decimal(row["units"])) if row["result"] == "L" else 0.0, axis=1)

    dados_filtrados["lucro_monetario"] = dados_filtrados["lucro_unidade"] * dados_filtrados["unidade_vigente"]

    dados_ate_ontem = dados_filtrados[dados_filtrados["date"] < datetime.today().date()]

    lucro_total_unidade_ate_ontem = dados_ate_ontem["lucro_unidade"].sum()
    total_unidades_apostadas_ate_ontem = dados_ate_ontem[
        (dados_ate_ontem["parlay"] == "N") & 
        (dados_ate_ontem["units"].notnull())
    ]["units"].sum()

    lucro_total_unidade = dados_filtrados["lucro_unidade"].sum()
    lucro_total_monetario = dados_filtrados["lucro_monetario"].sum()

    roi = (lucro_total_unidade / total_unidades_apostadas * 100) if total_unidades_apostadas > 0 else 0

    col1, col2, col5, spacer2 = st.columns([1, 2, 1, 6])
    with col1:
        st.metric("Total de Apostas", len(dados_filtrados[dados_filtrados["parlay"] == "N"]))
    with col2:
        st.metric("Record", f"{len(dados_filtrados[dados_filtrados['result'] == 'W'])}W" + "-" + f"{len(dados_filtrados[dados_filtrados['result'] == 'L'])}L"+ "-" + f"{len(dados_filtrados[dados_filtrados['result'] == 'R'])}R")
    with col5:
        st.metric("ROI (%)", f"{roi:.2f}%")


    col3, col4, spacer3, spacer4 = st.columns([1, 2, 3, 4])
    with col3:
        st.metric(
            label="Lucro Total (u)",
            value=f"{lucro_total_unidade:.2f}u",
        )
    with col4:
        st.metric(
            label="Lucro Total (R$)",
            value=f"R$ {lucro_total_monetario:.2f}"
        )

    spacer, spacer, spacer, spacer = st.columns([2, 2, 2, 2])
    spacer, spacer, spacer, spacer = st.columns([2, 2, 2, 2])
    spacer, spacer, spacer, spacer = st.columns([2, 2, 2, 2])
    spacer, spacer, spacer, spacer = st.columns([2, 2, 2, 2])

    hoje = datetime.today().date()
    ontem = hoje - timedelta(days=1)
    sete_dias_atras = hoje - timedelta(days=6)
    inicio_mes_atual = hoje.replace(day=1)

    # Função para montar o record
    def get_record_string(df):
        w = len(df[df["result"] == "W"])
        l = len(df[df["result"] == "L"])
        r = len(df[df["result"] == "R"])
        return f"{w}-{l}-{r}"

    # Subsets por período
    dados_hoje = dados_filtrados[dados_filtrados["date"] == hoje]
    dados_ontem = dados_filtrados[dados_filtrados["date"] == ontem]
    dados_7d = dados_filtrados[dados_filtrados["date"] >= sete_dias_atras]
    dados_mes = dados_filtrados[dados_filtrados["date"] >= inicio_mes_atual]

    # Lucro e recorde de hoje
    lucro_hoje_unidade = dados_hoje["lucro_unidade"].sum()
    lucro_hoje_monetario = dados_hoje["lucro_monetario"].sum()
    record_hoje = get_record_string(dados_hoje)

    # Lucro e recorde de ontem
    lucro_ontem_unidade = dados_ontem["lucro_unidade"].sum()
    lucro_ontem_monetario = dados_ontem["lucro_monetario"].sum()
    record_ontem = get_record_string(dados_ontem)

    # Lucro e recorde últimos 7 dias
    lucro_7d_unidade = dados_7d["lucro_unidade"].sum()
    lucro_7d_monetario = dados_7d["lucro_monetario"].sum()
    record_7d = get_record_string(dados_7d)

    # Lucro e recorde mês atual
    lucro_mes_unidade = dados_mes["lucro_unidade"].sum()
    lucro_mes_monetario = dados_mes["lucro_monetario"].sum()
    record_mes = get_record_string(dados_mes)

    # Exibir métricas com record
    col6, col7, col8, col9, spacer9 = st.columns([1, 1, 1, 1, 6])
    with col6:
        st.metric("Hoje", f"{lucro_hoje_unidade:.2f}u", delta=f"{lucro_hoje_monetario:.2f}")
        st.caption(f"&nbsp;&nbsp;{record_hoje}")
    with col7:
        st.metric("Ontem", f"{lucro_ontem_unidade:.2f}u", delta=f"{lucro_ontem_monetario:.2f}")
        st.caption(f"&nbsp;&nbsp;{record_ontem}")
    with col8:
        st.metric("Últimos 7", f"{lucro_7d_unidade:.2f}u", delta=f"{lucro_7d_monetario:.2f}")
        st.caption(f"&nbsp;&nbsp;{record_7d}")
    with col9:
        st.metric("Mês", f"{lucro_mes_unidade:.2f}u", delta=f"{lucro_mes_monetario:.2f}")
        st.caption(f"&nbsp;&nbsp;{record_mes}")

    # style_metric_cards(
    #     background_color="#1e1e1e",
    #     border_size_px=1,
    #     border_color="#e0e0e0",
    #     border_left_color="#FFFFFF",
    #     border_radius_px=12,
    #     box_shadow=True
    # )

    # Gráfico de lucro por dia (Unidades)
    lucro_diario = dados_filtrados.copy()
    lucro_diario["date"] = pd.to_datetime(lucro_diario["date"]).dt.date  
    lucro_diario = lucro_diario.groupby("date")["lucro_unidade"].sum().reset_index()
    lucro_diario["date"] = lucro_diario["date"].astype(str) 
    fig1 = px.line(lucro_diario, x="date", y="lucro_unidade", title="Lucro Diário (Unidades)")
    fig1.update_xaxes(type="category")  
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico de lucro acumulado diário (Unidades)
    lucro_acumulado = lucro_diario.copy()
    lucro_acumulado["lucro_acumulado"] = lucro_acumulado["lucro_unidade"].cumsum()  
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=lucro_acumulado["date"],
        y=lucro_acumulado["lucro_acumulado"],
        mode="lines",
        name="Lucro Acumulado",
        fill='tozeroy',  
        line=dict(color='green') 
    ))

    fig2.update_layout(
        title="Lucro Acumulado Diário (Unidades)",
        xaxis_title="Data",
        yaxis_title="Lucro Acumulado (u)",
    )
    fig2.update_xaxes(type="category")
    st.plotly_chart(fig2, use_container_width=True)

    # Gráfico de lucro por esporte
    lucro_por_sport = dados_filtrados.groupby("sport")["lucro_unidade"].sum().reset_index()
    fig3 = px.bar(lucro_por_sport, x="sport", y="lucro_unidade", title="Lucro por Esporte (Unidades)")
    st.plotly_chart(fig3, use_container_width=True)

    # Gráfico de resultado por capper
    resultado_capper = dados_filtrados.groupby("capper")["lucro_unidade"].sum().reset_index()
    fig4 = px.bar(resultado_capper, x="capper", y="lucro_unidade", title="Lucro por Capper (Unidades)")
    st.plotly_chart(fig4, use_container_width=True)

if aba == "Configurações":
    st.subheader("⚙️ Configurações")
    st.markdown("### Editar Configurações do Sistema")

    with st.form("form_configs"):
        st.markdown("#### Editar Bookies")
        novos_bookies = st.text_area("Adicione ou edite os Bookies (separados por vírgula)", value=",".join(BOOKIES))

        st.markdown("#### Editar Esportes")
        novos_esportes = st.text_area("Adicione ou edite os Esportes (separados por vírgula)", value=",".join(SPORTS))

        st.markdown("#### Editar Tipos de Aposta")
        novos_bet_types = st.text_area("Adicione ou edite os Tipos de Aposta (separados por vírgula)", value=",".join(BET_TYPES))

        st.markdown("#### Editar Cappers")
        novos_cappers = st.text_area("Adicione ou edite os Cappers (separados por vírgula)", value=",".join(CAPPERS))

        st.markdown("#### Editar Competições")
        novas_competicoes = st.text_area("Adicione ou edite as Competições (separados por vírgula)", value=",".join(COMPETITIONS))

        st.markdown("#### Editar Unidade de Aposta")
        nova_unidade = st.text_input("Valor da Unidade de Aposta (R$)", value=str(UNIDADE_APOSTA))

        submitted = st.form_submit_button("Salvar Configurações")

        if submitted:
            config["BOOKIES"] = [x.strip() for x in novos_bookies.split(",") if x.strip()]
            config["SPORTS"] = [x.strip() for x in novos_esportes.split(",") if x.strip()]
            config["BET_TYPES"] = [x.strip() for x in novos_bet_types.split(",") if x.strip()]
            config["CAPPERS"] = [x.strip() for x in novos_cappers.split(",") if x.strip()]
            config["COMPETITIONS"] = [x.strip() for x in novas_competicoes.split(",") if x.strip()]
            try:
                config["UNIDADE_APOSTA"] = float(nova_unidade)
            except ValueError:
                st.warning("Valor inválido para a unidade de aposta. Mantido valor anterior.")

            salvar_config(config)
            st.success("✅ Configurações salvas com sucesso!")