# views/receita/edit.py
import streamlit as st
from datetime import date, datetime
from models.receita import Receita
from services.receita_service import ReceitaService
from services.categoria_receita_service import CategoriaReceitaService
from services.conta_service import ContaService
from utils.message_handler import message_handler

def show_edit_receita(receita: Receita):
    """Exibe o formulário de edição de receita"""
    if not receita:
        st.error("Receita não encontrada")
        return
    
    receita_service = ReceitaService()
    categoria_service = CategoriaReceitaService()
    conta_service = ContaService()
    
    st.header("✏️ Editar Receita")
    st.subheader(f"Editando: {receita.descricao}")
    
    with st.form("form_edit_receita"):
        # Dados básicos da receita
        col1, col2 = st.columns(2)
        
        with col1:
            descricao = st.text_input(
                "Descrição*", 
                value=receita.descricao,
                placeholder="Ex: Salário, Freelance, Vendas...",
                max_chars=200,
                help="Descrição da receita (máximo 200 caracteres)"
            )
            
            valor = st.number_input(
                "Valor (R$)*", 
                value=float(receita.valor),
                min_value=0.01, 
                format="%.2f",
                help="Valor da receita em reais"
            )
            
        with col2:
            data_recebimento = st.date_input(
                "Data de Recebimento*", 
                value=receita.data_recebimento,
                help="Data em que a receita foi ou será recebida"
            )
            
            # Carrega categorias disponíveis
            categorias = categoria_service.listar_categorias()
            categoria_opcoes = {cat.nome: cat.id for cat in categorias}
            
            # Define a categoria atual como selecionada
            categoria_atual = receita.categoria.nome if receita.categoria else None
            categoria_index = 0
            if categoria_atual and categoria_atual in categoria_opcoes:
                categoria_index = list(categoria_opcoes.keys()).index(categoria_atual)
            
            categoria_selecionada = st.selectbox(
                "Categoria*",
                options=list(categoria_opcoes.keys()),
                index=categoria_index,
                help="Selecione a categoria da receita"
            )
        
        # Dados complementares
        col3, col4 = st.columns(2)
        
        with col3:
            # Carrega contas disponíveis
            contas = conta_service.listar_contas()
            conta_opcoes = {"Nenhuma conta selecionada": None}
            conta_opcoes.update({conta.nome: conta.id for conta in contas})
            
            # Define a conta atual como selecionada
            conta_atual = receita.conta.nome if receita.conta else None
            conta_index = 0
            if conta_atual and conta_atual in conta_opcoes:
                conta_index = list(conta_opcoes.keys()).index(conta_atual)
            
            conta_selecionada = st.selectbox(
                "Conta",
                options=list(conta_opcoes.keys()),
                index=conta_index,
                help="Conta onde a receita será creditada (opcional)"
            )
        
        with col4:
            pass  # Coluna para equilibrar o layout
            
        observacoes = st.text_area(
            "Observações",
            value=receita.observacoes if receita.observacoes else "",
            placeholder="Informações adicionais sobre a receita...",
            max_chars=1000,
            help="Observações complementares (opcional, máximo 1000 caracteres)"
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submit_button = st.form_submit_button(
                "💾 Salvar Alterações", 
                use_container_width=True,
                type="primary"
            )
            
        with col_btn2:
            cancel_button = st.form_submit_button(
                "❌ Cancelar", 
                use_container_width=True
            )
        
        # Processamento do formulário
        if submit_button:
            try:
                # Valida campos obrigatórios
                if not descricao.strip():
                    st.error("A descrição é obrigatória")
                    return
                
                if valor <= 0:
                    st.error("O valor deve ser maior que zero")
                    return
                
                if not categoria_selecionada:
                    st.error("Selecione uma categoria")
                    return
                
                # Prepara dados para atualização
                dados_atualizacao = {
                    'descricao': descricao.strip(),
                    'valor': valor,
                    'data_recebimento': data_recebimento,
                    'categoria_id': categoria_opcoes[categoria_selecionada],
                    'observacoes': observacoes.strip() if observacoes else None,
                    'conta_id': conta_opcoes[conta_selecionada] if conta_selecionada != "Nenhuma conta selecionada" else None
                }
                
                # Atualiza a receita
                receita_atualizada = receita_service.atualizar_receita(receita.id, dados_atualizacao)
                
                if receita_atualizada:
                    st.success("Receita atualizada com sucesso!")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao atualizar receita: {str(e)}")
        
        if cancel_button:
            st.rerun()
    
    # Informações adicionais
    st.divider()
    
    with st.expander("ℹ️ Informações da Receita"):
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write("**ID da Receita:**")
            st.write(receita.id)
            
        with col_info2:
            if hasattr(receita, 'created_at') and receita.created_at:
                st.write("**Data de Criação:**")
                st.write(receita.created_at.strftime('%d/%m/%Y %H:%M'))
        
        if hasattr(receita, 'updated_at') and receita.updated_at:
            st.write("**Última Atualização:**")
            st.write(receita.updated_at.strftime('%d/%m/%Y %H:%M'))