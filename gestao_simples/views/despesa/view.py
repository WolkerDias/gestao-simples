# views/despesa/view.py
import streamlit as st
from datetime import datetime, date
from models.despesa import Despesa
from services.despesa_service import DespesaService
#from views.despesa.edit import show_edit_despesa

def show_view_despesa(despesa: Despesa):
    """Exibe os detalhes de uma despesa específica"""
    if not despesa:
        st.error("Despesa não encontrada")
        return
    
    despesa_service = DespesaService()
    
    st.header(f"📋 Detalhes da Despesa")
    st.subheader(f"🏷️ {despesa.descricao}")
    
    # Status visual da despesa
    if despesa.paga:
        st.success("✅ Despesa Paga")
    else:
        # Verifica se está vencida
        if despesa.data_vencimento < date.today():
            st.error("🚨 Despesa Vencida")
        else:
            st.warning("⏳ Despesa Pendente")
    
    # Informações principais em colunas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Valor",
            value=f"R$ {despesa.valor:.2f}"
        )
    
    with col2:
        st.metric(
            label="📅 Vencimento",
            value=despesa.data_vencimento.strftime('%d/%m/%Y')
        )
    
    with col3:
        pagamento_label = "Pagamento" if despesa.paga else "Status"
        pagamento_value = despesa.data_pagamento.strftime('%d/%m/%Y') if despesa.data_pagamento else "Pendente"
        
        st.metric(
            label=f"📋 {pagamento_label}",
            value=pagamento_value
        )
    
    # Informações complementares
    st.divider()
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.write("**🏷️ Categoria:**")
        st.write(despesa.categoria.nome if despesa.categoria else "Não informada")
        
    with col5:
        st.write("**🏦 Conta:**")
        st.write(despesa.conta.nome if despesa.conta else "Não informada")
        
    with col6:
        st.write("**📝 Data de Criação:**")
        st.write(despesa.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(despesa, 'created_at') else "Não disponível")
    
    # Observações
    if despesa.observacoes:
        st.write("**💭 Observações:**")
        st.text_area(
            "",
            value=despesa.observacoes,
            disabled=True,
            height=100,
            label_visibility="collapsed"
        )
    
    st.divider()
    
    # Botões de ação
    if despesa.paga:
        col_edit, col_delete, col_back = st.columns([1, 1, 1])
    else:
        col_pay, col_edit, col_delete, col_back = st.columns([1, 1, 1, 1])
        
        with col_pay:
            if st.button("✅ Marcar como Paga", use_container_width=True, type="primary"):
                try:
                    despesa_service.marcar_despesa_como_paga(despesa.id)
                    st.success("Despesa marcada como paga!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao marcar como paga: {str(e)}")
    
    with col_edit:
        if st.button("✏️ Editar", use_container_width=True):
            #show_edit_despesa(despesa)
            pass
    
    with col_delete:
        if st.button("🗑️ Excluir", use_container_width=True, type="secondary"):
            show_delete_confirmation_despesa(despesa.id)
    
    with col_back:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.rerun()

def show_delete_confirmation_despesa(despesa_id: int):
    """Exibe confirmação de exclusão de despesa"""
    despesa_service = DespesaService()
    
    st.warning("⚠️ Confirmação de Exclusão")
    st.write("Tem certeza que deseja excluir esta despesa? Esta ação não pode ser desfeita.")
    
    col_confirm, col_cancel = st.columns(2)
    
    with col_confirm:
        if st.button("✅ Sim, Excluir", use_container_width=True, type="primary"):
            try:
                despesa_service.deletar_despesa(despesa_id)
                st.success("Despesa excluída com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir despesa: {str(e)}")
    
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()