# views/categoria_despesa/view.py
import streamlit as st
from models.categoria_despesa import CategoriaDespesa
from services.categoria_despesa_service import CategoriaDespesaService
from views.categoria_despesa.edit import show_edit_categoria_despesa

def show_view_categoria_despesa(categoria: CategoriaDespesa):
    """Exibe os detalhes de uma categoria de despesa específica"""
    if not categoria:
        st.error("Categoria não encontrada")
        return
    
    categoria_service = CategoriaDespesaService()
    
    st.header(f"📋 Detalhes da Categoria")
    st.subheader(f"🏷️ {categoria.nome}")
    
    # Informações principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="📋 ID",
            value=categoria.id
        )
    
    with col2:
        # Obtém estatísticas da categoria (incluindo contagem de despesas)
        count_despesas = categoria_service.contar_despesas_por_categoria(categoria.id)
        st.metric(
            label="📊 Quantidade de Despesas",
            value=count_despesas
        )
    
    # Descrição
    if categoria.descricao:
        st.divider()
        st.write("**📝 Descrição:**")
        st.text_area(
            "",
            value=categoria.descricao,
            disabled=True,
            height=100,
            label_visibility="collapsed"
        )
    
    st.divider()
    
    # Informações adicionais
    if hasattr(categoria, 'created_at') and categoria.created_at:
        st.write("**📅 Data de Criação:**")
        st.write(categoria.created_at.strftime('%d/%m/%Y %H:%M'))
    
    if hasattr(categoria, 'updated_at') and categoria.updated_at:
        st.write("**🔄 Última Atualização:**")
        st.write(categoria.updated_at.strftime('%d/%m/%Y %H:%M'))
    
    st.divider()
    
    # Botões de ação
    col_edit, col_delete, col_back = st.columns([1, 1, 1])
    
    with col_edit:
        if st.button("✏️ Editar", use_container_width=True):
            show_edit_categoria_despesa(categoria)
    
    with col_delete:
        if st.button("🗑️ Excluir", use_container_width=True, type="secondary"):
            show_delete_confirmation_categoria_despesa(categoria.id)
    
    with col_back:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.rerun()

def show_delete_confirmation_categoria_despesa(categoria_id: int):
    """Exibe confirmação de exclusão de categoria de despesa"""
    categoria_service = CategoriaDespesaService()
    
    st.warning("⚠️ Confirmação de Exclusão")
    st.write("Tem certeza que deseja excluir esta categoria? Esta ação não pode ser desfeita e removerá a categoria de todas as despesas associadas.")
    
    # Verifica se pode excluir
    pode_excluir, motivo = categoria_service.validar_exclusao_categoria(categoria_id)
    
    if not pode_excluir:
        st.error(motivo)
        return
    
    col_confirm, col_cancel = st.columns(2)
    
    with col_confirm:
        if st.button("✅ Sim, Excluir", use_container_width=True, type="primary"):
            try:
                categoria_service.deletar_categoria(categoria_id)
                st.success("Categoria excluída com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir categoria: {str(e)}")
    
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()