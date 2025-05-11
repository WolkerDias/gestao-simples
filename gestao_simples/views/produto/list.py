# views/produto/list.py
import streamlit as st
import pandas as pd
from services.produto_service import ProdutoService
from services.produto_service import ProdutoService
from views.produto.create import show_create_produto
from views.produto.view import show_view_produto
from utils.message_handler import message_handler

class ProdutoListView:
    def __init__(self):
        self.produto_service = ProdutoService()
        self.render()

    def render(self):
        st.title("📦 Gestão de Produtos")
        message_handler.display_toast_message()        

        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Produto", use_container_width=True):
                show_create_produto()

        # Preparar dados
        produtos = self.produto_service.listar_produtos()

        if not produtos:
            st.info("Nenhum produto cadastrado")
            return
        
        df_produtos = pd.DataFrame([{
            'ID': p.id, 
            'Nome': p.nome, 
            'Medida': p.unidade_medida,
            'Descrição': p.descricao
        } for p in produtos])


        # Renderizar DataFrame com seleção
        produto = st.dataframe(
            df_produtos,
            use_container_width=True,
            key="data",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        selected_row = produto.selection.rows

        if selected_row:
            disabled = False
        else:
            disabled = True
            
        with col2:
            if st.button("👁️ Detalhes", use_container_width=True, help="Selecione um item para visualizar!", disabled=disabled):
                produto_id = df_produtos.loc[selected_row]['ID'].values[0]
                produto = self.produto_service.buscar_produto_por_id(produto_id)
                show_view_produto(produto)