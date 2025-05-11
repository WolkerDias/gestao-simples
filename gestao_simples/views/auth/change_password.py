# views/auth/change_password.py
import streamlit as st
from services.auth_service import AuthService
from utils.message_handler import message_handler, MessageType

auth_service = AuthService()

@st.dialog("🔒 Alterar Senha", width="small")
def change_password_view():    
    with st.form("change_password_form"):
        old_password = st.text_input("Senha atual", type="password")
        new_password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirme a nova senha", type="password")
        submitted = st.form_submit_button("Alterar", icon=":material/edit:")
        
        if submitted:
            if new_password != confirm_password:
                st.error("As senhas não coincidem")
                return

            auth_service = AuthService()
            usuario = auth_service.buscar_usuario_por_id(st.session_state.usuario["id"])

            if not usuario.verificar_senha(old_password):
                st.error("Senha atual incorreta")
                return
                
            usuario.senha = new_password
            auth_service.atualizar_senha(usuario, new_password)
            message_handler.add_message(
                MessageType.SUCCESS,
                "Senha alterada com sucesso!"
            )
            st.rerun()