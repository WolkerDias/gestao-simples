# utils/message_handler.py
import streamlit as st
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from utils.logger import logger  # Importando o logger configurado

class MessageType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Message:
    type: MessageType
    text: str
    icon: str
    timestamp: datetime = datetime.now()

class MessageHandler:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def add_message(self, message_type: MessageType, text: str):
        """
        Adiciona uma mensagem para ser exibida como toast na tela principal
        """
        icon = {
            MessageType.SUCCESS: "✅",
            MessageType.ERROR: "❌",
            MessageType.WARNING: "⚠️",
            MessageType.INFO: "ℹ️"
        }[message_type]
        
        # Armazenar para exibição na tela principal como toast
        st.session_state.message = text
        st.session_state.icon = icon
        
        # Registrar no log usando o logger configurado
        if message_type == MessageType.ERROR:
            logger.error(text)
        elif message_type == MessageType.WARNING:
            logger.warning(text)
        else:
            logger.info(text)
    
    def display_toast_message(self):
        """Exibe o toast na tela principal e remove a mensagem"""
        if "message" in st.session_state:
            icon = st.session_state.get("icon", "✅")
            st.toast(st.session_state.message, icon=icon)
            # Limpar as mensagens após exibir
            del st.session_state.message
            del st.session_state.icon

message_handler = MessageHandler()  # Singleton instance