# views/conta/create.py
import streamlit as st
from services.conta_service import ContaService

@st.dialog("Nova Conta", width="medium")
def show_create_conta():
    """Exibe o formulário de criação de conta"""
    conta_service = ContaService()
    
    st.header("🏦 Nova Conta")
    
    with st.form("form_conta", clear_on_submit=True):
        nome = st.text_input(
            "Nome*", 
            placeholder="Ex: Banco X, Carteira, Poupança...",
            max_chars=100,
            help="Nome da conta (máximo 100 caracteres)"
        )
        
        tipo = st.selectbox(
            "Tipo*",
            options=["Banco", "Carteira", "Poupança", "Investimento", "Outro"],
            help="Selecione o tipo da conta"
        )
        
        saldo_inicial = st.number_input(
            "Saldo Inicial (R$)*", 
            min_value=0.00, 
            value=0.00,
            format="%.2f",
            help="Saldo inicial da conta em reais"
        )
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submit_button = st.form_submit_button(
                "💾 Salvar", 
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
                if not nome.strip():
                    st.error("O nome é obrigatório")
                    return
                
                # Prepara dados para criação
                dados_conta = {
                    'nome': nome.strip(),
                    'tipo': tipo,
                    'saldo_inicial': saldo_inicial
                }
                
                # Cria a conta
                conta_service.criar_conta(dados_conta)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar conta: {str(e)}")
        
        if cancel_button:
            st.rerun()