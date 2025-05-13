from twilio.rest import Client
from dotenv import load_dotenv
import os
import re

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

FROM_WHATSAPP = "whatsapp:+14155238886"  # Número do sandbox da Twilio
MEU_NUMERO_WHATSAPP = "whatsapp:+5522997776367"  # Seu número pessoal

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def formatar_numero(numero):
    """
    Formata o número de telefone para o padrão internacional do WhatsApp
    
    Args:
        numero (str): Número de telefone do cliente (ex: 22998562940)
    
    Returns:
        str: Número formatado (ex: whatsapp:+5522998562940)
    """
    # Remove tudo que não é dígito
    apenas_numeros = ''.join(filter(str.isdigit, numero))
    
    # Verifica se já tem o código do país (55)
    if not apenas_numeros.startswith("55"):
        apenas_numeros = "55" + apenas_numeros
    
    return f"whatsapp:+{apenas_numeros}"

def enviar_mensagem(destino, mensagem):
    """
    Envia mensagem via WhatsApp usando a API da Twilio
    
    Args:
        destino (str): Número de telefone do destinatário
        mensagem (str): Texto da mensagem a ser enviada
    
    Returns:
        str: SID da mensagem ou mensagem de erro
    """
    try:
        destino_formatado = formatar_numero(destino)
        
        # Verifica se o número tem o tamanho correto (55 + DDD + número)
        if len(''.join(filter(str.isdigit, destino_formatado))) < 12:
            return "Erro: Número de telefone inválido"
        
        msg = client.messages.create(
            body=mensagem,
            from_=FROM_WHATSAPP,
            to=destino_formatado
        )
        return msg.sid
    except Exception as e:
        return f"Erro: {str(e)}"

def enviar_lembrete(destino, nome, data, horario):
    """
    Envia mensagem de lembrete no dia anterior ao agendamento
    
    Args:
        destino (str): Número de WhatsApp do cliente
        nome (str): Nome do cliente
        data (str): Data do agendamento (YYYY-MM-DD)
        horario (str): Horário do agendamento (HH:MM)
    
    Returns:
        str: SID da mensagem ou mensagem de erro
    """
    mensagem = (
        f"Olá, {nome}! 😊\n\n"
        f"Este é apenas um lembrete sobre seu agendamento:\n"
        f"📅 Amanhã, {data}\n"
        f"🕒 Às {horario}\n\n"
        f"Caso precise remarcar ou cancelar, entre em contato conosco.\n\n"
        f"Até amanhã! 🌞"
    )
    return enviar_mensagem(destino, mensagem)