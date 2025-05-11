# views/auth/login.py
import streamlit as st
from services.auth_service import AuthService
from utils.logger import logger

@st.dialog("🔐 Login", width="large")
def login_view():
    
    with st.form("login_form"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            auth_service = AuthService()
            try:
                usuario = auth_service.autenticar(email, senha)
                token = auth_service.criar_token(usuario)
                st.session_state.token = token
                st.session_state.usuario = usuario.__dict__
                st.rerun()
            except Exception as e:
                logger.error(f"Falha no login: {str(e)}")
                st.error("Credenciais inválidas ou usuário desativado")