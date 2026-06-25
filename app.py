import streamlit as st
import pandas as pd

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(page_title="Agente NR-12", page_icon="🤖")

st.title("🤖 Agente NR-12 Inteligente")
st.write("Sistema analítico NR-12 completo")

# =========================
# CARREGAR DADOS
# =========================
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel("Banco de Dados PWBI 2026.xlsx")

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
        st.error(f"Erro ao carregar base: {e}")
        return pd.DataFrame()

df = carregar_dados()

# =========================
# FUNÇÕES DE TRATAMENTO
# =========================
def tratar(valor):
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", ""]:
        return "informação faltante"
    return str(valor).strip()

def tratar_status(valor):
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", ""]:
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
# MEMÓRIA CHAT
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# FUNÇÃO PRINCIPAL
# =========================
def responder(pergunta):
    p = pergunta.lower()

    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }

    try:

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

✅ **PWT adequadas:**
{lista_ok if lista_ok else "Nenhum"}

---

🔴 **PWT NÃO adequadas:**
{lista_pendente if lista_pendente else "Nenhum"}
"""

        # =========================
        # 🏢 FORNECEDOR (VISUAL NOVO ✅)
        # =========================
        for fornecedor in df["FORNECEDOR"].dropna().unique():

            if str(fornecedor).lower() in p:

                df_f = df[df["FORNECEDOR"] == fornecedor]

                status = df_f["STATUS AR :"].fillna("").astype(str).str.upper()

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
{tratar(df_f.get("CONTA SAP").dropna().iloc[0]) if "CONTA SAP" in df.columns and df_f["CONTA SAP"].notna().any() else "informação faltante"}

📄 PO:
{tratar(df_f.get("PO").dropna().iloc[0]) if "PO" in df.columns and df_f["PO"].notna().any() else "informação faltante"}
"""

        # =========================
        # 📊 STATUS AR (LISTA ✅)
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
        # 🔎 PWT (VISUAL MELHORADO ✅)
        # =========================
        for palavra in p.split():
            if palavra.isnumeric():

                for _, row in df.iterrows():
                    if palavra in " ".join([str(v) for v in row.values]):

                        return f"""
🔎 **PWT {palavra}**

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

        return "🤖 Não consegui interpretar. Tente mês, fornecedor, PWT ou status AR."

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