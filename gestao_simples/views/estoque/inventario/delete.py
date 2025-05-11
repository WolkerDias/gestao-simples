# views/estoque/inventario/delete.py

import streamlit as st
from utils.message_handler import message_handler, MessageType
from utils.logger import logger


# Função de diálogo para confirmação de exclusão
@st.dialog("⚠️ Atenção:")
def confirm_delete_dialog(inventario_id, inventario_referencia, service):
    st.warning(f"O inventario **{inventario_referencia}** será deletado do banco de dados. Deseja continuar?", icon="⚠️")
    
    # Botões de confirmação dentro do diálogo
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Deletar", type="primary"):
            try:                    
                service.deletar_inventario(inventario_id)
                message_handler.add_message(
                    MessageType.INFO,
                    f"Inventário **{inventario_referencia}** excluído com sucesso!"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir Inventário: {e}")                
                logger.error(f"Erro ao excluir Inventário: {str(e)}")
    
    with col_cancel:
        if st.button("Cancelar"):
            st.rerun()  # Fecha o diálogo sem fazer nada