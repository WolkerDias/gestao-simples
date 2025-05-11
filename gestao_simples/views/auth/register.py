# views/auth/register.py
import streamlit as st
from services.auth_service import AuthService
from models.usuario import Usuario
from utils.message_handler import message_handler, MessageType

auth_service = AuthService()

@st.dialog("👤 Cadastrar Novo Usuário", width="large")
def register_view():
    
    with st.form("register_form"):
        nome = st.text_input("Nome completo")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        is_admin = st.checkbox("Administrador")
        submitted = st.form_submit_button("Cadastrar")
        
    if submitted:
        try:
            # Cria um Usuario
            novo_usuario = Usuario(
                nome=nome,
                email=email,
                is_admin=is_admin,
                ativo=True
            )
            novo_usuario.senha = senha  # Gera o hash via setter

            auth_service.criar_usuario(novo_usuario)

            # Se chegou aqui, deu sucesso
            message_handler.add_message(
                MessageType.SUCCESS,
                f"Usuário {nome} cadastrado com sucesso!"
            )
            
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao cadastrar: {str(e)}")