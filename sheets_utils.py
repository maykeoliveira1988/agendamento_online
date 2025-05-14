import gspread
import streamlit as st
from google.oauth2 import service_account

# Autenticação com base nas secrets do Streamlit
def conectar_planilha(nome_planilha):
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        cliente = gspread.authorize(creds)
        planilha = cliente.open(nome_planilha)
        return planilha
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        st.stop()

def ler_configuracoes():
    planilha = conectar_planilha("Agendamentos")
    aba = planilha.worksheet("configuracoes")
    dados = aba.get_all_records()
    configuracoes = {}
    for linha in dados:
        data = linha['data']
        bloqueado = linha['bloqueado'] == 'TRUE'
        horarios = linha['horarios_disponiveis'].split(",") if linha['horarios_disponiveis'] else []
        configuracoes[data] = {
            "bloqueado": bloqueado,
            "horarios_disponiveis": horarios
        }
    return configuracoes

def salvar_configuracoes(configuracoes):
    planilha = conectar_planilha("Agendamentos")
    aba = planilha.worksheet("configuracoes")
    linhas = []
    for data, config in configuracoes.items():
        linhas.append([
            data,
            "TRUE" if config["bloqueado"] else "FALSE",
            ",".join(config["horarios_disponiveis"])
        ])
    aba.clear()
    aba.append_row(["data", "bloqueado", "horarios_disponiveis"])
    for linha in linhas:
        aba.append_row(linha)

def ler_reservas():
    planilha = conectar_planilha("Agendamentos")
    aba = planilha.worksheet("reservas")
    dados = aba.get_all_records()
    reservas = {}
    for linha in dados:
        data = linha['data']
        if data not in reservas:
            reservas[data] = []
        reservas[data].append(linha['info'])
    return reservas

def salvar_reservas(reservas):
    planilha = conectar_planilha("Agendamentos")
    aba = planilha.worksheet("reservas")
    linhas = []
    for data, lista in reservas.items():
        for reserva in lista:
            linhas.append([data, reserva])
    aba.clear()
    aba.append_row(["data", "info"])
    for linha in linhas:
        aba.append_row(linha)
