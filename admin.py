import streamlit as st
import json
import os
from datetime import datetime
import re
import shutil
from dotenv import load_dotenv  # Adicionado para carregar o .env

# Carregar variáveis de ambiente do .env
load_dotenv()  # Adicionado para garantir que o .env seja lido

# Arquivos
ARQUIVO_CONFIG = "datas_configuradas.json"
ARQUIVO_RESERVAS = "reservas.json"
PASTA_BACKUP = "backups"

# Horários possíveis
TODOS_HORARIOS = [
    "08:00", "09:00", "10:00", "11:00", "12:00",
    "13:00", "14:00", "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00", "21:00"
]

# Funções utilitárias
def carregar_json(caminho):
    """Carrega um arquivo JSON, retornando um dicionário vazio se o arquivo estiver vazio, não existir ou for inválido"""
    if not os.path.exists(caminho):
        return {}
    
    try:
        # Tentar abrir com UTF-8 (padrão)
        with open(caminho, "r", encoding='utf-8-sig') as f:
            conteudo = f.read().strip()
            if not conteudo:
                return {}
            return json.loads(conteudo)
    except UnicodeDecodeError:
        # Se falhar, tentar UTF-16
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
        st.write(f"Salvando dados em {caminho}...")
        with open(caminho, "w", encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False

def criar_backup():
    if not os.path.exists(PASTA_BACKUP):
        os.makedirs(PASTA_BACKUP)
    
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    for arquivo in [ARQUIVO_CONFIG, ARQUIVO_RESERVAS]:
        if os.path.exists(arquivo):
            nome_backup = f"{data_hora}_{arquivo}"
            shutil.copy2(arquivo, os.path.join(PASTA_BACKUP, nome_backup))

def check_password():
    """Verifica se o usuário digitou a senha correta"""
    def password_entered():
        senha_ambiente = os.getenv("ADMIN_PASSWORD")
        if not senha_ambiente:
            st.error("A senha não foi carregada do .env. Verifique o arquivo.")
            st.stop()
        if st.session_state["password"] == senha_ambiente:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    
    if "password_correct" not in st.session_state:
        st.text_input(
            "Senha de administrador", 
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Senha de administrador", 
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("😕 Senha incorreta")
        return False
    else:
        return True

# Verificar autenticação
if not check_password():
    st.stop()

# Carregar dados
configuracoes = carregar_json(ARQUIVO_CONFIG)
reservas = carregar_json(ARQUIVO_RESERVAS)

# Interface
st.title("🛠️ Painel Administrativo de Agendamento")

# Menu de navegação
menu = st.sidebar.selectbox("Menu", ["Configurações", "Relatórios", "Backups"])

if menu == "Configurações":
    # Seleção de data
    data = st.date_input("📅 Escolha a data para configurar")
    data_str = data.strftime("%Y-%m-%d")

    # Carregar configuração existente
    config_do_dia = configuracoes.get(data_str, {
        "bloqueado": False,
        "horarios_disponiveis": []
    })

    # Interface de configuração
    bloqueado = st.checkbox("🔒 Bloquear esse dia para agendamento", value=config_do_dia.get("bloqueado", False))

    if not bloqueado:
        horarios_selecionados = st.multiselect(
            "🕑 Horários disponíveis para este dia",
            options=TODOS_HORARIOS,
            default=config_do_dia.get("horarios_disponiveis", [])
        )
    else:
        horarios_selecionados = []

    # Botão para salvar configurações
    if st.button("💾 Salvar Configuração"):
        configuracoes[data_str] = {
            "bloqueado": bloqueado,
            "horarios_disponiveis": horarios_selecionados
        }
        salvar_json(configuracoes, ARQUIVO_CONFIG)
        criar_backup()
        st.success(f"✅ Configuração salva para {data_str}")

    # Mostrar agendamentos do dia
    st.subheader("📋 Agendamentos do dia selecionado")
    reservas_do_dia = reservas.get(data_str, [])
    
    if reservas_do_dia:
        for i, r in enumerate(reservas_do_dia, 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{i}. 🕒 {r}")
            with col2:
                if st.button(f"❌ Cancelar {i}", key=f"cancel_{i}"):
                    with st.expander("⚠️ Confirmação"):
                        st.warning(f"Tem certeza que deseja cancelar este agendamento?\n{r}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✅ Sim, cancelar {i}"):
                                reserva_cancelada = reservas_do_dia.pop(i-1)
                                reservas[data_str] = reservas_do_dia
                                salvar_json(reservas, ARQUIVO_RESERVAS)
                                criar_backup()
                                st.success(f"Agendamento cancelado: {reserva_cancelada}")
                                st.experimental_rerun()
                        with col2:
                            if st.button("❌ Não cancelar"):
                                st.info("Operação cancelada")
        
        if st.button("🧹 Limpar TODOS os agendamentos deste dia"):
            with st.expander("⚠️ Confirmação"):
                st.warning("Tem certeza que deseja apagar TODOS os agendamentos deste dia?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Sim, apagar tudo"):
                        reservas[data_str] = []
                        salvar_json(reservas, ARQUIVO_RESERVAS)
                        criar_backup()
                        st.warning(f"⚠️ Todos os agendamentos do dia {data_str} foram apagados.")
                        st.experimental_rerun()
                with col2:
                    if st.button("❌ Cancelar"):
                        st.info("Operação cancelada")
    else:
        st.info("Nenhum agendamento para este dia.")

elif menu == "Relatórios":
    st.subheader("📊 Relatórios de Agendamentos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data de início")
    with col2:
        data_fim = st.date_input("Data de fim")
    
    if st.button("Gerar Relatório"):
        datas_relatorio = [
            (datetime.strptime(data, "%Y-%m-%d").date(), data)
            for data in reservas.keys() 
            if datetime.strptime(data, "%Y-%m-%d").date() >= data_inicio and 
               datetime.strptime(data, "%Y-%m-%d").date() <= data_fim
        ]
        
        if not datas_relatorio:
            st.warning("Nenhum agendamento no período selecionado")
        else:
            total_reservas = 0
            for data_date, data_str in sorted(datas_relatorio):
                reservas_dia = reservas.get(data_str, [])
                total_reservas += len(reservas_dia)
                st.markdown(f"### {data_str} ({len(reservas_dia)} agendamentos)")
                for reserva in reservas_dia:
                    st.markdown(f"- {reserva}")
            
            st.success(f"Total de agendamentos no período: {total_reservas}")

elif menu == "Backups":
    st.subheader("💾 Backups do Sistema")
    
    if os.path.exists(PASTA_BACKUP):
        backups = sorted(os.listdir(PASTA_BACKUP), reverse=True)
        
        st.info(f"Total de backups disponíveis: {len(backups)}")
        
        backup_selecionado = st.selectbox(
            "Selecione um backup para visualizar ou restaurar",
            backups
        )
        
        if backup_selecionado:
            caminho_backup = os.path.join(PASTA_BACKUP, backup_selecionado)
            with open(caminho_backup, 'r', encoding='utf-8-sig') as f:
                conteudo = json.load(f)
            st.json(conteudo)
            
            if st.button("Restaurar este backup"):
                arquivo_original = ARQUIVO_CONFIG if ARQUIVO_CONFIG in backup_selecionado else ARQUIVO_RESERVAS
                shutil.copy2(caminho_backup, arquivo_original)
                st.success(f"Backup {backup_selecionado} restaurado com sucesso!")
                st.experimental_rerun()
    else:
        st.warning("Nenhum backup encontrado.")
