# views/conta/view.py
import streamlit as st
from models.conta import Conta
from services.conta_service import ContaService
from views.conta.edit import show_edit_conta

def show_view_conta(conta: Conta):
    """Exibe os detalhes de uma conta específica"""
    if not conta:
        st.error("Conta não encontrada")
        return
    
    conta_service = ContaService()
    
    st.header(f"📋 Detalhes da Conta")
    st.subheader(f"🏦 {conta.nome}")
    
    # Informações principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📋 ID",
            value=conta.id
        )
    
    with col2:
        st.metric(
            label="🏷️ Tipo",
            value=conta.tipo
        )
    
    with col3:
        st.metric(
            label="💰 Saldo Inicial",
            value=f"R$ {conta.saldo_inicial:.2f}"
        )
    
    st.divider()
    
    # Informações adicionais
    col4, col5 = st.columns(2)
    
    with col4:
        st.write("**📅 Data de Criação:**")
        st.write(conta.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(conta, 'created_at') else "Não disponível")
    
    with col5:
        st.write("**🔄 Última Atualização:**")
        st.write(conta.updated_at.strftime('%d/%m/%Y %H:%M') if hasattr(conta, 'updated_at') else "Não disponível")
    
    st.divider()
    
    # Botões de ação
    col_edit, col_delete, col_back = st.columns([1, 1, 1])
    
    with col_edit:
        if st.button("✏️ Editar", use_container_width=True):
            show_edit_conta(conta)
    
    with col_delete:
        if st.button("🗑️ Excluir", use_container_width=True, type="secondary"):
            show_delete_confirmation_conta(conta.id)
    
    with col_back:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.rerun()

def show_delete_confirmation_conta(conta_id: int):
    """Exibe confirmação de exclusão de conta"""
    conta_service = ContaService()
    
    st.warning("⚠️ Confirmação de Exclusão")
    st.write("Tem certeza que deseja excluir esta conta? Esta ação não pode ser desfeita e removerá a conta de todas as transações associadas.")
    
    col_confirm, col_cancel = st.columns(2)
    
    with col_confirm:
        if st.button("✅ Sim, Excluir", use_container_width=True, type="primary"):
            try:
                conta_service.deletar_conta(conta_id)
                st.success("Conta excluída com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir conta: {str(e)}")
    
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()