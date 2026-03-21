# views/receita/create.py
import streamlit as st
from datetime import date, datetime
from services.receita_service import ReceitaService
from services.categoria_receita_service import CategoriaReceitaService
from services.conta_service import ContaService
from utils.message_handler import message_handler

@st.dialog("Nova Receita", width="large")
def show_create_receita():
    """Exibe o formulário de criação de receita"""
    receita_service = ReceitaService()
    categoria_service = CategoriaReceitaService()
    conta_service = ContaService()
    
    st.header("📝 Cadastrar Nova Receita")
    
    with st.form("form_receita", clear_on_submit=True):
        # Dados básicos da receita
        col1, col2 = st.columns(2)
        
        with col1:
            descricao = st.text_input(
                "Descrição*", 
                placeholder="Ex: Salário, Freelance, Vendas...",
                max_chars=200,
                help="Descrição da receita (máximo 200 caracteres)"
            )
            
            valor = st.number_input(
                "Valor (R$)*", 
                min_value=0.01, 
                format="%.2f",
                help="Valor da receita em reais"
            )
            
        with col2:
            data_recebimento = st.date_input(
                "Data de Recebimento*", 
                value=date.today(),
                format="DD/MM/YYYY",
                help="Data em que a receita foi ou será recebida"
            )
            
            # Carrega categorias disponíveis
            categorias = categoria_service.listar_categorias()
            categoria_opcoes = {cat.nome: cat.id for cat in categorias}
            
            categoria_selecionada = st.selectbox(
                "Categoria*",
                options=list(categoria_opcoes.keys()),
                help="Selecione a categoria da receita"
            )
        
        # Dados complementares
        col3, col4 = st.columns(2)
        
        with col3:
            # Carrega contas disponíveis
            contas = conta_service.listar_contas()
            conta_opcoes = {"Selecione uma conta": None}
            conta_opcoes.update({conta.nome: conta.id for conta in contas})
            
            conta_selecionada = st.selectbox(
                "Conta",
                options=list(conta_opcoes.keys()),
                help="Conta onde a receita será creditada (opcional)"
            )
        
        with col4:
            pass  # Coluna para equilibrar o layout
            
        observacoes = st.text_area(
            "Observações",
            placeholder="Informações adicionais sobre a receita...",
            max_chars=1000,
            help="Observações complementares (opcional, máximo 1000 caracteres)"
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submit_button = st.form_submit_button(
                "💾 Salvar Receita", 
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
                
                # Prepara dados para criação
                dados_receita = {
                    'descricao': descricao.strip(),
                    'valor': valor,
                    'data_recebimento': data_recebimento,
                    'categoria_id': categoria_opcoes[categoria_selecionada],
                    'observacoes': observacoes.strip() if observacoes else None,
                    'conta_id': conta_opcoes[conta_selecionada] if conta_selecionada != "Selecione uma conta" else None
                }
                
                # Cria a receita
                receita_service.criar_receita(dados_receita)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar receita: {str(e)}")
        
        if cancel_button:
            st.rerun()