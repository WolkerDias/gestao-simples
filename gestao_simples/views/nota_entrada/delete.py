# views/nota_entrada/delete.py

import streamlit as st
from utils.message_handler import message_handler, MessageType
from utils.logger import logger


# Função de diálogo para confirmação de exclusão
@st.dialog("⚠️ Atenção:")
def confirm_delete_dialog(nota_entrada_id, service):
    st.warning("O item selecionado será deletado do banco de dados. Deseja continuar?")
    
    # Botões de confirmação dentro do diálogo
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Deletar", type="primary"):
            try:                    
                service.deletar_nota_entrada(nota_entrada_id)
                message_handler.add_message(
                    MessageType.INFO,
                    f"Nota de entrada excluída com sucesso!"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir Nota de entrada: {e}")                
                logger.error(f"Erro ao excluir Nota de entrada: {str(e)}")
    
    with col_cancel:
        if st.button("Cancelar"):
            st.rerun()  # Fecha o diálogo sem fazer nada