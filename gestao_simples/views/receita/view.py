# views/receita/view.py
import streamlit as st
from datetime import datetime
from models.receita import Receita
from services.receita_service import ReceitaService
from views.receita.edit import show_edit_receita

def show_view_receita(receita: Receita):
    """Exibe os detalhes de uma receita específica"""
    if not receita:
        st.error("Receita não encontrada")
        return
    
    receita_service = ReceitaService()
    
    st.header(f"📋 Detalhes da Receita")
    st.subheader(f"🏷️ {receita.descricao}")
    
    # Informações principais em colunas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Valor",
            value=f"R$ {receita.valor:.2f}"
        )
    
    with col2:
        st.metric(
            label="📅 Data Recebimento",
            value=receita.data_recebimento.strftime('%d/%m/%Y')
        )
    
    with col3:
        st.metric(
            label="🏷️ Categoria",
            value=receita.categoria.nome if receita.categoria else "Não informada"
        )
    
    # Informações complementares
    st.divider()
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.write("**🏦 Conta:**")
        st.write(receita.conta.nome if receita.conta else "Não informada")
        
    with col5:
        st.write("**📝 Data de Criação:**")
        st.write(receita.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(receita, 'created_at') else "Não disponível")
    
    # Observações
    if receita.observacoes:
        st.write("**💭 Observações:**")
        st.text_area(
            "",
            value=receita.observacoes,
            disabled=True,
            height=100,
            label_visibility="collapsed"
        )
    
    st.divider()
    
    # Botões de ação
    col_edit, col_delete, col_back = st.columns([1, 1, 1])
    
    with col_edit:
        if st.button("✏️ Editar", use_container_width=True):
            show_edit_receita(receita)
    
    with col_delete:
        if st.button("🗑️ Excluir", use_container_width=True, type="secondary"):
            show_delete_confirmation_receita(receita.id)
    
    with col_back:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.rerun()

def show_delete_confirmation_receita(receita_id: int):
    """Exibe confirmação de exclusão de receita"""
    receita_service = ReceitaService()
    
    st.warning("⚠️ Confirmação de Exclusão")
    st.write("Tem certeza que deseja excluir esta receita? Esta ação não pode ser desfeita.")
    
    col_confirm, col_cancel = st.columns(2)
    
    with col_confirm:
        if st.button("✅ Sim, Excluir", use_container_width=True, type="primary"):
            try:
                receita_service.deletar_receita(receita_id)
                st.success("Receita excluída com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir receita: {str(e)}")
    
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()