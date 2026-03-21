# views/categoria_receita/create.py
import streamlit as st
from services.categoria_receita_service import CategoriaReceitaService
from utils.message_handler import message_handler

@st.dialog("Nova Categoria de Receita", width="medium")
def show_create_categoria_receita():
    """Exibe o formulário de criação de categoria de receita"""
    categoria_service = CategoriaReceitaService()
    
    st.header("📝 Nova Categoria de Receita")
    
    with st.form("form_categoria_receita", clear_on_submit=True):
        nome = st.text_input(
            "Nome*", 
            placeholder="Ex: Salário, Freelance, Vendas...",
            max_chars=100,
            help="Nome da categoria (máximo 100 caracteres)"
        )
        
        descricao = st.text_area(
            "Descrição",
            placeholder="Descreva a categoria...",
            max_chars=255,
            help="Descrição opcional (máximo 255 caracteres)"
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
                dados_categoria = {
                    'nome': nome.strip(),
                    'descricao': descricao.strip() if descricao else None
                }
                
                # Cria a categoria
                categoria_service.criar_categoria(dados_categoria)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar categoria: {str(e)}")
        
        if cancel_button:
            st.rerun()