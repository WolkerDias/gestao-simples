# views/auth/view.py
import streamlit as st
from services.auth_service import AuthService

@st.dialog("Visualizar Usuário", width="large")
def show_view_usuario(usuario):
    auth_service = AuthService()

    # Edição
    with st.container():
        with st.form("editar_usuario"):
            nome = st.text_input("Nome do Usuário", value=usuario.nome)
            email = st.text_input("E-mail", value=usuario.email)

            col1, col2 = st.columns(2)
            is_admin = col1.checkbox("Administrador", value=usuario.is_admin)
            ativo = col2.checkbox("Ativo", value=usuario.ativo)

            submitted = st.form_submit_button("Atualizar")
            
            if submitted:
                usuario.nome = nome
                usuario.email = email or None
                usuario.is_admin = is_admin
                usuario.ativo = ativo

                auth_service.atualizar_usuario(usuario)
                
                st.rerun()