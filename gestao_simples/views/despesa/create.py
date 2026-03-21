# views/despesa/create.py
import streamlit as st
from datetime import date, datetime
from services.despesa_service import DespesaService
from services.categoria_despesa_service import CategoriaDespesaService
from services.conta_service import ContaService
from utils.message_handler import message_handler

@st.dialog("Nova Despesa", width="large")
def show_create_despesa():
    """Exibe o formulário de criação de despesa"""
    despesa_service = DespesaService()
    categoria_service = CategoriaDespesaService()
    conta_service = ContaService()
    
    st.header("📝 Cadastrar Nova Despesa")
    
    with st.form("form_despesa", clear_on_submit=True):
        # Dados básicos da despesa
        col1, col2 = st.columns(2)
        
        with col1:
            descricao = st.text_input(
                "Descrição*", 
                placeholder="Ex: Conta de luz, Aluguel, Supermercado...",
                max_chars=200,
                help="Descrição da despesa (máximo 200 caracteres)"
            )
            
            valor = st.number_input(
                "Valor (R$)*", 
                min_value=0.01, 
                format="%.2f",
                help="Valor da despesa em reais"
            )
            
        with col2:
            data_vencimento = st.date_input(
                "Data de Vencimento*", 
                value=date.today(),
                help="Data de vencimento da despesa"
            )
            
            # Carrega categorias disponíveis
            categorias = categoria_service.listar_categorias()
            categoria_opcoes = {cat.nome: cat.id for cat in categorias}
            
            categoria_selecionada = st.selectbox(
                "Categoria*",
                options=list(categoria_opcoes.keys()),
                help="Selecione a categoria da despesa"
            )
        
        # Status de pagamento
        col3, col4 = st.columns(2)
        
        with col3:
            paga = st.checkbox(
                "Despesa já foi paga?",
                help="Marque se a despesa já foi quitada"
            )
            
            data_pagamento = None
            if paga:
                data_pagamento = st.date_input(
                    "Data de Pagamento",
                    value=date.today(),
                    help="Data em que a despesa foi paga"
                )
        
        with col4:
            # Carrega contas disponíveis
            contas = conta_service.listar_contas()
            conta_opcoes = {"Selecione uma conta": None}
            conta_opcoes.update({conta.nome: conta.id for conta in contas})
            
            conta_selecionada = st.selectbox(
                "Conta",
                options=list(conta_opcoes.keys()),
                help="Conta de onde a despesa será debitada (opcional)"
            )
            
        observacoes = st.text_area(
            "Observações",
            placeholder="Informações adicionais sobre a despesa...",
            max_chars=1000,
            help="Observações complementares (opcional, máximo 1000 caracteres)"
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submit_button = st.form_submit_button(
                "💾 Salvar Despesa", 
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
                dados_despesa = {
                    'descricao': descricao.strip(),
                    'valor': valor,
                    'data_vencimento': data_vencimento,
                    'categoria_id': categoria_opcoes[categoria_selecionada],
                    'observacoes': observacoes.strip() if observacoes else None,
                    'conta_id': conta_opcoes[conta_selecionada] if conta_selecionada != "Selecione uma conta" else None,
                    'paga': paga,
                    'data_pagamento': data_pagamento if paga else None
                }
                
                # Cria a despesa
                despesa_service.criar_despesa(dados_despesa)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar despesa: {str(e)}")
        
        if cancel_button:
            st.rerun()