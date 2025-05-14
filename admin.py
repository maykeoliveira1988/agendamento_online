import streamlit as st
import shutil
from datetime import datetime
from dotenv import load_dotenv  # Adicionado para carregar o .env
from sheets_utils import ler_configuracoes, salvar_configuracoes, ler_reservas, salvar_reservas

# Carregar variáveis de ambiente do .env
load_dotenv()  # Adicionado para garantir que o .env seja lido

# Funções utilitárias
def check_password():
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
        st.text_input("Senha de administrador", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha de administrador", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta")
        return False
    else:
        return True

# Verificar autenticação
if not check_password():
    st.stop()

# Carregar dados do Google Sheets
configuracoes = ler_configuracoes()  # Agora vem do Google Sheets
reservas = ler_reservas()  # Agora vem do Google Sheets

# Interface
st.title("🛠️ Painel Administrativo de Agendamento")

# Menu de navegação
menu = st.sidebar.selectbox("Menu", ["Configurações", "Relatórios", "Backups"])

if menu == "Configurações":
    data = st.date_input("📅 Escolha a data para configurar")
    data_str = data.strftime("%Y-%m-%d")

    config_do_dia = configuracoes.get(data_str, {
        "bloqueado": False,
        "horarios_disponiveis": []
    })

    bloqueado = st.checkbox("🔒 Bloquear esse dia para agendamento", value=config_do_dia.get("bloqueado", False))

    if not bloqueado:
        horarios_selecionados = st.multiselect(
            "🕑 Horários disponíveis para este dia",
            options=TODOS_HORARIOS,
            default=config_do_dia.get("horarios_disponiveis", [])
        )
    else:
        horarios_selecionados = []

    if st.button("💾 Salvar Configuração"):
        configuracoes[data_str] = {
            "bloqueado": bloqueado,
            "horarios_disponiveis": horarios_selecionados
        }
        st.write("Configuração a ser salva:", configuracoes)  # DEBUG

        if salvar_configuracoes(configuracoes):
            st.success(f"✅ Configuração salva para {data_str}")
        else:
            st.error("❌ Falha ao salvar a configuração. Verifique permissões e o console.")

    # Agendamentos
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
                                salvar_reservas(reservas)
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
                        salvar_reservas(reservas)
                        st.warning(f"⚠️ Todos os agendamentos do dia {data_str} foram apagados.")
                        st.experimental_rerun()
                with col2:
                    if st.button("❌ Cancelar"):
                        st.info("Operação cancelada")
    else:
        st.info("Nenhum agendamento para este dia.")
