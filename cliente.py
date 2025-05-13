import streamlit as st
import json
import os
from datetime import datetime
import re
import threading
import base64

st.set_page_config(
    page_title="Agendamento Online",
    page_icon="👙",
    layout="centered",  # Layout sem sidebar
    initial_sidebar_state="collapsed"  # Garante que a sidebar não apareça
)
def set_background(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    css = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.55)),
                    url("data:image/png;base64,{encoded}") no-repeat center center fixed;
        background-size: cover;
    }}

    .stTextInput > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > input,
    .stTextArea textarea {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: #ffffff !important;
        border: 1px solid #d86b82;
        border-radius: 10px;
    }}

    .stButton > button {{
        background-color: #d86b82;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        border: none;
    }}

    .stMarkdown h1, .stTitle, .stHeader {{
        color: #ff578a !important;
    }}

    label, .stTextInput label, .stDateInput label {{
        color: #ffffff !important;
        font-weight: bold;
    }}

    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown strong,
    .stMarkdown {{
        color: #ffffff !important;
    }}

    .stCheckbox > label {{
        color: #ffffff !important;
        font-weight: bold;
    }}

    .st-expanderHeader {{
        color: #ffffff !important;
        font-weight: bold;
    }}

    .stAlert {{
        color: #ffffff !important;
    }}

    a {{
        color: #d86b82 !important;
        font-weight: bold;
        text-decoration: underline;
    }}

    footer, footer p {{
        color: #ffffff !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Chamada
set_background("images/imagem_fundo.png")


ARQUIVO_CONFIG = "datas_configuradas.json"
ARQUIVO_RESERVAS = "reservas.json"
reserva_lock = threading.Lock()

def carregar_json(caminho):
    """Carrega um arquivo JSON, retornando um dicionário vazio se o arquivo estiver vazio, não existir ou for inválido"""
    if not os.path.exists(caminho):
        return {}
    
    try:
        with open(caminho, "r", encoding='utf-8-sig') as f:
            conteudo = f.read().strip()
            if not conteudo:
                return {}
            return json.loads(conteudo)
    except UnicodeDecodeError:
        try:
            with open(caminho, "r", encoding='utf-16') as f:
                conteudo = f.read().strip()
                if not conteudo:
                    return {}
                return json.loads(conteudo)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo {caminho}: {e}")
            return {}
    except json.JSONDecodeError as e:
        st.error(f"Arquivo JSON inválido em {caminho}: {e}")
        return {}
    except Exception as e:
        st.error(f"Erro inesperado ao carregar {caminho}: {e}")
        return {}

def salvar_json(dados, caminho):
    """Salva dados em um arquivo JSON com formatação correta"""
    try:
        with open(caminho, "w", encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

def validar_whatsapp(numero):
    """Valida se o número de WhatsApp está no formato correto (DDD + número) e retorna o número formatado com 55"""
    numero_limpo = ''.join(filter(str.isdigit, numero))
    if len(numero_limpo) == 10 or len(numero_limpo) == 11:  # Aceita 10 (DDD + 8) ou 11 (DDD + 9) dígitos
        if len(numero_limpo) == 10 and numero_limpo.startswith(('21', '22', '24', '27', '28')):  # Exemplos de DDDs válidos
            return f"55{numero_limpo}"
        elif len(numero_limpo) == 11 and numero_limpo[2:].startswith(('9')):  # Verifica DDD + 9 dígitos (celular)
            return f"55{numero_limpo}"
    return None  # Retorna None se inválido

def validar_email(email):
    """Valida o formato do e-mail se fornecido"""
    if not email:
        return True
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# Carregar dados
configuracoes = carregar_json(ARQUIVO_CONFIG)
reservas = carregar_json(ARQUIVO_RESERVAS)

# Número de WhatsApp para contato (seu número real)
WHATSAPP_CONTATO = "22997776367"  # Número real fornecido
whatsapp_contato_formatado = validar_whatsapp(WHATSAPP_CONTATO)

st.title("👙 Agendamento Online")
st.markdown("Reserve seu horário de bronzeamento")

# Seção de data
data = st.date_input("📅 Escolha a Data*", min_value=datetime.today())
data_str = data.strftime("%Y-%m-%d")
st.markdown(f"📌 Data selecionada: **{data_str}**")

# Verificar disponibilidade
configuracao = configuracoes.get(data_str, {})
bloqueado = configuracao.get("bloqueado", False)
horarios_config = configuracao.get("horarios_disponiveis", [])
horarios_reservados = reservas.get(data_str, [])
horarios_disponiveis = [h for h in horarios_config if h not in horarios_reservados]

if bloqueado:
    st.error("⛔ Esta data está bloqueada para agendamento.")
elif not horarios_disponiveis:
    st.error("❌ Nenhum horário disponível nesta data.")

# Formulário de agendamento
with st.form("form_agendamento"):
    nome = st.text_input("Nome Completo*", placeholder="Seu nome completo")
    whatsapp = st.text_input("WhatsApp* (ex.: 22998562940)", placeholder="22999999999")
    email = st.text_input("E-mail (opcional)", placeholder="seu@email.com")

    if not bloqueado and horarios_disponiveis:
        horario = st.selectbox("Horário*", horarios_disponiveis)
    else:
        horario = None

    servico = st.selectbox(
        "Escolha o serviço*",
        [
            "1 Sessão Bronzeamento - R$100,00",
            "2 Sessões Bronzeamento - R$180,00",
            "3 Sessões Bronzeamento - R$240,00",
            "Esfoliação Corporal - R$40,00",
            "Banho de Lua - R$30,00"
        ]
    )

    # Termos e condições
    aceito = st.checkbox("Li e aceito os termos de cancelamento*")
    
    submit_button = st.form_submit_button("RESERVAR HORÁRIO")

    if submit_button:
        erros = []
        if not nome:
            erros.append("Nome completo é obrigatório")
        numero_formatado = validar_whatsapp(whatsapp)
        if not numero_formatado:
            erros.append("WhatsApp inválido. Use o formato DDD + número (ex.: 22998562940 ou 2299862940)")
        if not validar_email(email):
            erros.append("E-mail inválido")
        if not horario:
            erros.append("Selecione um horário disponível")
        if not aceito:
            erros.append("Você deve aceitar os termos de cancelamento")
        
        if erros:
            for erro in erros:
                st.error(erro)
        else:
            with reserva_lock:
                # Carregar configurações e reservas novamente dentro do lock para evitar inconsistências
                configuracoes_atualizadas = carregar_json(ARQUIVO_CONFIG)
                reservas_atualizadas = carregar_json(ARQUIVO_RESERVAS)
                horarios_reservados_atual = reservas_atualizadas.get(data_str, [])

                if horario in [r.split(" - ")[0] for r in horarios_reservados_atual]:
                    st.error(
                        "❌ Este horário acabou de ser reservado por outra pessoa.\n"
                        "Por favor, escolha outro horário disponível."
                    )
                else:
                    # Adicionar a nova reserva
                    nova_reserva = f"{horario} - {nome} ({numero_formatado}) - {servico}"
                    reservas_atualizadas.setdefault(data_str, []).append(nova_reserva)
                    salvar_json(reservas_atualizadas, ARQUIVO_RESERVAS)

                    # Remover o horário da lista de disponíveis
                    config_do_dia = configuracoes_atualizadas.get(data_str, {"horarios_disponiveis": []})
                    if not config_do_dia.get("bloqueado", False) and horario in config_do_dia.get("horarios_disponiveis", []):
                        config_do_dia["horarios_disponiveis"].remove(horario)
                        configuracoes_atualizadas[data_str] = config_do_dia
                        salvar_json(configuracoes_atualizadas, ARQUIVO_CONFIG)

                    st.success(
                        "✅ Horário reservado com sucesso!\n\n"
                        f"**Data:** {data_str}\n"
                        f"**Horário:** {horario}\n"
                        f"**Serviço:** {servico}\n\n"
                        "Anote seu horário, pois não enviaremos confirmações automáticas no momento."
                    )

# Termos e condições
with st.expander("📝 Termos e Condições"):
    st.markdown("""
    ### Política de Cancelamento:
    
    1. Cancelamentos devem ser feitos com pelo menos 24 horas de antecedência.
    2. Não comparecer no horário agendado resultará na perda do valor pago.
    3. Remarcações estão sujeitas à disponibilidade de horários.
    
    ### Política de Pagamento:
    
    1. O pagamento é realizado no local, no dia do serviço.
    2. Aceitamos dinheiro, PIX e cartões de crédito/débito.
    3. Não trabalhamos com planos de fidelidade ou mensalidades.
    
    Ao marcar seu horário, você concorda com estes termos.
    """)

# Rodapé com contato WhatsApp
st.markdown("---")
if whatsapp_contato_formatado:
    st.markdown(
        f"📞 Entre em contato pelo WhatsApp: [Clique aqui](https://wa.me/{whatsapp_contato_formatado})"
    )
st.markdown("© 2024 Helena Cola Bronze - Todos os direitos reservados")
