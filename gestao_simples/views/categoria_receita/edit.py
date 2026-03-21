# views/categoria_receita/edit.py
import streamlit as st
from models.categoria_receita import CategoriaReceita
from services.categoria_receita_service import CategoriaReceitaService

def show_edit_categoria_receita(categoria: CategoriaReceita):
    """Exibe o formulário de edição de categoria de receita"""
    if not categoria:
        st.error("Categoria não encontrada")
        return
    
    categoria_service = CategoriaReceitaService()
    
    st.header("✏️ Editar Categoria de Receita")
    st.subheader(f"Editando: {categoria.nome}")
    
    with st.form("form_edit_categoria_receita"):
        nome = st.text_input(
            "Nome*", 
            value=categoria.nome,
            placeholder="Ex: Salário, Freelance, Vendas...",
            max_chars=100,
            help="Nome da categoria (máximo 100 caracteres)"
        )
        
        descricao = st.text_area(
            "Descrição",
            value=categoria.descricao if categoria.descricao else "",
            placeholder="Descreva a categoria...",
            max_chars=255,
            help="Descrição opcional (máximo 255 caracteres)"
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
                if not nome.strip():
                    st.error("O nome é obrigatório")
                    return
                
                # Prepara dados para atualização
                dados_atualizacao = {
                    'nome': nome.strip(),
                    'descricao': descricao.strip() if descricao else None
                }
                
                # Atualiza a categoria
                categoria_atualizada = categoria_service.atualizar_categoria(categoria.id, dados_atualizacao)
                
                if categoria_atualizada:
                    st.success("Categoria atualizada com sucesso!")
                    st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao atualizar categoria: {str(e)}")
        
        if cancel_button:
            st.rerun()
    
    # Informações adicionais
    st.divider()
    
    with st.expander("ℹ️ Informações da Categoria"):
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write("**ID da Categoria:**")
            st.write(categoria.id)
            
        with col_info2:
            if hasattr(categoria, 'created_at') and categoria.created_at:
                st.write("**Data de Criação:**")
                st.write(categoria.created_at.strftime('%d/%m/%Y %H:%M'))
        
        if hasattr(categoria, 'updated_at') and categoria.updated_at:
            st.write("**Última Atualização:**")
            st.write(categoria.updated_at.strftime('%d/%m/%Y %H:%M'))