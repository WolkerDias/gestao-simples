# views/auth/delete.py

import streamlit as st
from utils.message_handler import message_handler, MessageType
from utils.logger import logger


# Função de diálogo para confirmação de exclusão
@st.dialog("⚠️ Atenção:")
def confirm_delete_dialog(usuario_id, usuario_nome, service):
    st.warning(f"O usuário **{usuario_nome}** será deletado do banco de dados. Deseja continuar?", icon="⚠️")

    # Botões de confirmação dentro do diálogo
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Deletar", type="primary", use_container_width=True):
            try:
                service.deletar_usuario(usuario_id)
                message_handler.add_message(
                    MessageType.INFO,
                    f"Usuário **{usuario_nome}** excluído com sucesso!"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir Usuário: {e}")
                logger.error(f"Erro ao excluir Usuário: {str(e)}")

    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()  # Fecha o diálogo sem fazer nada