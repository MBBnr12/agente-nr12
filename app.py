import streamlit as st
import pandas as pd
from datetime import datetime

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(page_title="Agente NR-12", page_icon="🤖")

st.title("🤖 Agente NR-12 Inteligente")
st.write("Sistema analítico NR-12 completo")

# =========================
# 📘 MENU LATERAL
# =========================

st.sidebar.title("📘 Guia Rápido")

st.sidebar.markdown("""
### Exemplos de Consulta

🔧 **PWT / Inventário**
EX: 56000

🏢 **Fornecedor**
EX: Vetor

🏭 **Centro de Custo**
EX: cc 174/4

📊 **Status AR**
EX: Status AR

🚨 **Máquinas Críticas**
EX: Máquinas críticas

📅 **Mês**
EX: Julho

💰 **Relatório Financeiro**
EX: Relatorio financeiro
""")

st.sidebar.info("""
💡 Dica

Utilize sempre:

✅ cc 174/4

para consultar Centros de Custo.

Isso evita conflito com consultas de PWT.

Você pode pesquisar por PWT, Inventário, Fornecedor, Centro de Custo, Mês, Máquinas críticas ou Status AR.
""")

# =========================
# BASE PRINCIPAL
# =========================
@st.cache_data
def carregar_dados():

    try:

        df = pd.read_excel("Banco de Dados PWBI.xlsx")

        df.columns = df.columns.astype(str).str.strip().str.upper()
        df = df.dropna(how="all")

        for col in [
            "ADEQUAÇÃO PREVISTA",
            "ADEQUAÇÃO REALIZADA",
            "PRÉ PROJETO ENTREGUE EM:",
            "AR ENTREGUE EM:"
        ]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    except Exception as e:
        st.error(f"Erro base principal: {e}")
        return pd.DataFrame()

# =========================
# BASE CENTRO DE CUSTO
# =========================
@st.cache_data
def carregar_cc():

    try:

        df_cc = pd.read_excel("base_cc.xlsx")

        df_cc.columns = (
            df_cc.columns
            .astype(str)
            .str.strip()
            .str.upper()
        )

        return df_cc

    except Exception as e:
        st.warning(f"Erro base CC: {e}")
        return pd.DataFrame()

df = carregar_dados()
df_cc = carregar_cc()

# =========================
# TRATAMENTO
# =========================
def tratar(valor):
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", ""]:
        return "informação faltante"
    return str(valor).strip()

def tratar_status(valor):
    if pd.isna(valor):
        return "Não avaliado"
    return str(valor).strip()

def formatar_data(valor):
    if pd.isna(valor):
        return "informação faltante"
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except:
        return str(valor)

# =========================
# MEMÓRIA
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# FUNÇÃO PRINCIPAL
# =========================
def responder(pergunta):

    p = pergunta.lower()

    meses = {
        "janeiro":1,"fevereiro":2,"março":3,"abril":4,
        "maio":5,"junho":6,"julho":7,"agosto":8,
        "setembro":9,"outubro":10,"novembro":11,"dezembro":12
    }

    try:
        
        # =========================
        # 🏢 CENTRO DE CUSTO
        # =========================
        if not df_cc.empty and (
             "cc" in p
            or "centro de custo" in p
        ):

            pesquisa_cc = (
                p.lower()
                .replace("centro de custo", "")
                .replace("cc", "")
                .replace("c.c", "")
                .replace("/", "")
                .replace(" ", "")
                .replace(".0", "")
                .strip()
            )

            for _, row in df_cc.iterrows():

                cc = (
                    str(row.get("CENTRO DE CUSTO"))
                    .replace(".0", "")
                    .strip()
                )

                if cc == pesquisa_cc:

                    # Exibição interna
                    cc_exibicao = cc

                    if len(cc) == 4 and cc.isdigit():
                        cc_exibicao = f"{cc[:3]}/{cc[-1]}"

                    # Planejador principal
                    planejador_cols = [
                        "PLANEJADOR",
                        "PLANEJADOR 2",
                        "PLANEJADOR 3",
                        "PLANEJADOR 4",
                        "PLANEJADOR 5"
                    ]

                    planejador = next(
                        (
                            tratar(row[col])
                            for col in planejador_cols
                            if col in df_cc.columns and pd.notna(row[col])
                        ),
                        "informação faltante"
                    )

                    # Supervisor principal
                    supervisor_cols = [
                        "SUPERVISOR",
                        "SUPERVISOR 2",
                        "SUPERVISOR 3"
                    ]

                    supervisor = next(
                        (
                            tratar(row[col])
                            for col in supervisor_cols
                            if col in df_cc.columns and pd.notna(row[col])
                        ),
                        "informação faltante"
                    )

                    predio = tratar(row.get("PREDIO"))

                    try:
                        predio = str(int(float(predio)))
                    except:
                        pass

                    total_maquinas = 0

                    if "CENTRO DE CUSTO" in df.columns:

                        cc_base = (
                            df["CENTRO DE CUSTO"]
                            .fillna("")
                            .astype(str)
                            .str.upper()
                            .str.replace("CC", "", regex=False)
                            .str.replace("/", "", regex=False)
                            .str.replace(".0", "", regex=False)
                            .str.replace(" ", "", regex=False)
                            .str.strip()
                        )

                        cc_pesquisa = (
                            str(cc)
                            .upper()
                            .replace("CC", "")
                            .replace("/", "")
                            .replace(".0", "")
                            .replace(" ", "")
                            .strip()
                        )   
                    
                        total_maquinas = (cc_base == cc_pesquisa).sum()

                    return f"""
🏢 **C.C {cc_exibicao}**

📍 Prédio:
{predio}

👤 Supervisor:
{supervisor}

🧠 Planejador:
{planejador}

📊 Máquinas cadastradas:
{total_maquinas}
"""
        # =========================
        # 🔴 MÁQUINAS CRÍTICAS
        # =========================
        if "criticas" in p or "críticas" in p:

            hoje = pd.Timestamp.now()
            col_pwt = "SICK" if "SICK" in df.columns else "INVENTÁRIO"

            atrasadas = df[
                (df["ADEQUAÇÃO PREVISTA"].notna()) &
                (df["ADEQUAÇÃO PREVISTA"] < hoje) &
                (df["ADEQUAÇÃO REALIZADA"].isna())
            ]

            lista_atrasadas = "\n".join(
                [f":red[{x}]" for x in atrasadas[col_pwt].dropna().astype(str).head(15)]
            )

            status = df["STATUS AR :"].fillna("").astype(str).str.strip()
            nao = df[status == ""]

            lista_nao = "\n".join(
                [f":red[{x}]" for x in nao[col_pwt].dropna().astype(str).head(15)]
            )

            return f"""
🚨 **MÁQUINAS CRÍTICAS**

🔴 Máquinas ATRASADAS:
{len(atrasadas)}

PWTs:
{lista_atrasadas if lista_atrasadas else "Nenhuma"}

---

⚠️ Máquinas NÃO AVALIADAS:
{len(nao)}

PWTs:
{lista_nao if lista_nao else "Nenhuma"}
"""

        # =========================
        # 📅 MÊS
        # =========================
        for nome, num in meses.items():
            if nome in p:

                df_mes = df[df["ADEQUAÇÃO PREVISTA"].dt.month == num]

                col_pwt = "SICK" if "SICK" in df.columns else "INVENTÁRIO"

                ok = df_mes[df_mes["ADEQUAÇÃO REALIZADA"].notna()]
                pendente = df_mes[df_mes["ADEQUAÇÃO REALIZADA"].isna()]

                lista_ok = "\n".join(ok[col_pwt].dropna().astype(str).head(10))
                lista_pendente = "\n".join(
                    [f":red[{x}]" for x in pendente[col_pwt].dropna().astype(str).head(10)]
                )

                return f"""
📅 **ANÁLISE DE {nome.upper()}**

📊 Total previstas:
{len(df_mes)}

✅ Máquinas adequadas:
{len(ok)}

📐 Pré-projetos validados:
{df_mes["VALIDAÇÃO DO PRÉ PROJETO"].notna().sum() if "VALIDAÇÃO DO PRÉ PROJETO" in df.columns else 0}

---

✅ PWT adequadas:
{lista_ok if lista_ok else "Nenhum"}

---

🔴 PWT não adequadas:
{lista_pendente if lista_pendente else "Nenhum"}
"""
            
        # =========================
        # 🏢 FORNECEDOR
        # =========================
        for fornecedor in df["FORNECEDOR"].dropna().unique():

             if str(fornecedor).lower() in p:

                df_f = df[df["FORNECEDOR"] == fornecedor]

                status = df_f["STATUS AR :"].fillna("").astype(str).str.upper()

                conta_sap = "informação faltante"
                po = "informação faltante"

                if "CONTA SAP" in df.columns:
                    valores_sap = df_f["CONTA SAP"].dropna()

                    if len(valores_sap) > 0:
                        conta_sap = str(valores_sap.iloc[0])

                if "PO" in df.columns:
                    valores_po = df_f["PO"].dropna()

                    if len(valores_po) > 0:
                        po = str(valores_po.iloc[0])

                        return f"""
🏢 **FORNECEDOR: {fornecedor.upper()}**

📊 Total de máquinas:
{len(df_f)}

✅ AR aprovadas:
{status.str.contains("APROVADO").sum()}

❌ AR reprovadas:
{status.str.contains("REPROVADO").sum()}

📐 Pré-projetos validados:
{df_f["VALIDAÇÃO DO PRÉ PROJETO"].notna().sum() if "VALIDAÇÃO DO PRÉ PROJETO" in df.columns else 0}

✅ Máquinas adequadas:
{df_f["ADEQUAÇÃO REALIZADA"].notna().sum()}

💼 Conta SAP:
{conta_sap}

📄 PO:
{po}
"""

        # =========================
        # 📊 STATUS AR
        # =========================
        if "status ar" in p:

            status = df["STATUS AR :"].fillna("").astype(str).str.upper()

            return f"""
📊 **STATUS DAS ARs**

✅ Aprovadas:
{status.str.contains("APROVADO").sum()}

⚠️ Condicionais:
{status.str.contains("CONDICIONAL").sum()}

❌ Reprovadas:
{status.str.contains("REPROVADO").sum()}

⏳ Não avaliadas:
{(status == "").sum()}
"""
        
        # =========================
        # 🔎 BUSCA PWT + INVENTÁRIO
        # =========================
        for termo in p.split():
    
            for _, row in df.iterrows():
        
                valores = " ".join([str(v) for v in row.values]).lower()
        
                if termo in valores:
        
                    return f"""
🔎 **PWT {termo}**
        
🛠️ Máquina:
{tratar(row.get("NOME DA MAQUINA"))}
        
🏢 Centro de Custo:
{tratar(row.get("CENTRO DE CUSTO"))}
        
🤝 Fornecedor:
{tratar(row.get("FORNECEDOR"))}
        
✅ Adequada?
{"Sim" if pd.notna(row.get("ADEQUAÇÃO REALIZADA")) else "Não"}

📐 Pré-projeto:
{formatar_data(row.get("PRÉ PROJETO ENTREGUE EM:"))}
        
📄 NF:
{tratar(row.get("NF"))}
        
📊 Status AR:
{tratar_status(row.get("STATUS AR :"))}
        
📅 Data AR Inicial:
{formatar_data(row.get("AR ENTREGUE EM:"))}
        
📄 AR Final:
Não avaliado
        
📅 Data AR Final:
informação faltante
"""
        # =========================
        # 💰 RELATÓRIO FINANCEIRO
        # =========================
        if "relatório financeiro" in p or "relatorio financeiro" in p:

            resultado = "💰 **RELATÓRIO FINANCEIRO NR-12**\n\n"

            meses_nomes = {
                1: "JANEIRO",
                2: "FEVEREIRO",
                3: "MARÇO",
                4: "ABRIL",
                5: "MAIO",
                6: "JUNHO",
                7: "JULHO",
                8: "AGOSTO",
                9: "SETEMBRO",
                10: "OUTUBRO",
                11: "NOVEMBRO",
                12: "DEZEMBRO"
            }

            meses_existentes = sorted(
                df["ADEQUAÇÃO PREVISTA"]
                .dropna()
                .dt.month
                .unique()
            )

            for mes in meses_existentes:

                nome_mes = meses_nomes.get(mes, f"MÊS {mes}")

                df_mes = df[
                    (df["ADEQUAÇÃO PREVISTA"].notna()) &
                    (df["ADEQUAÇÃO PREVISTA"].dt.month == mes)
                ]

                soma_10 = pd.to_numeric(
                    df_mes["10% LAUDO"],
                    errors="coerce"
                ).fillna(0).sum()

                soma_90 = pd.to_numeric(
                    df_mes["90% MATERIAL"],
                    errors="coerce"
                ).fillna(0).sum()

                total_previsto = soma_10 + soma_90

                resultado += f"""
📅 **{nome_mes}/2026**

💵 Soma dos 10% Laudo:
R$ {soma_10:,.2f}

💵 Soma dos 90% Material:
R$ {soma_90:,.2f}

📊 Total Previsto:
R$ {total_previsto:,.2f}

--------------------------------

"""
            return resultado
        
        return "🤖 Não consegui interpretar."
    except Exception as e:
        return f"⚠️ Erro: {e}"
# =========================
# CHAT
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Pergunte sobre NR-12...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    resposta = responder(user_input)

    st.session_state.messages.append({"role": "assistant", "content": resposta})

    with st.chat_message("assistant"):
        st.markdown(resposta)