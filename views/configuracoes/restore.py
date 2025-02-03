# views/configuracoes/restore.py

import streamlit as st
from config.database import restore_database
from utils.message_handler import message_handler, MessageType
from services.restore_service import save_last_restore
from utils.logger import logger


# Função de diálogo para confirmação de restauração
@st.dialog("⚠️ Atenção:")
def confirm_restore_dialog(backup_path):
    st.warning("A restauração irá substituir todos os dados atuais do banco. Deseja continuar?")
    
    # Botões de confirmação dentro do diálogo
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Confirmar Restauração", type="primary"):
            try:
                restore_database(backup_path)
                # Salva a última restauração no arquivo JSON
                save_last_restore(backup_path)
                
                # Se chegou aqui, deu sucesso
                message_handler.add_message(
                    MessageType.SUCCESS,
                    f"Backup {backup_path} restaurado com sucesso!"
                )                
                st.rerun()  # Atualiza a página para refletir as mudanças
            except Exception as e:
                st.error(f"Erro ao restaurar backup: {str(e)}")
                logger.error(f"Restore error: {str(e)}")
    
    with col_cancel:
        if st.button("Cancelar"):
            st.rerun()  # Fecha o diálogo sem fazer nada