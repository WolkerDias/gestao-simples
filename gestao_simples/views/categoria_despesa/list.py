# views/categoria_despesa/list.py
import streamlit as st
import pandas as pd
from services.categoria_despesa_service import CategoriaDespesaService
from views.categoria_despesa.create import show_create_categoria_despesa
from views.categoria_despesa.view import show_view_categoria_despesa

class CategoriaDespesaListView:
    def __init__(self):
        self.categoria_service = CategoriaDespesaService()
        self.render()

    def render(self):
        st.title("🏷️ Categorias de Despesa")
        st.divider()
        
        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Categoria", use_container_width=True):
                show_create_categoria_despesa()

        # Preparar dados
        categorias = self.categoria_service.listar_categorias()

        if not categorias:
            st.info("Nenhuma categoria cadastrada")
            return
        
        # Criar DataFrame com as categorias
        df_categorias = pd.DataFrame([{
            'ID': cat.id, 
            'Nome': cat.nome, 
            'Descrição': cat.descricao if cat.descricao else '-',
            'Qtd. Despesas': self.categoria_service.contar_despesas_por_categoria(cat.id)
        } for cat in categorias])

        # Renderizar DataFrame com seleção
        categoria_table = st.dataframe(
            df_categorias,
            use_container_width=True,
            key="data_categorias_despesa",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        selected_row = categoria_table.selection.rows

        if selected_row:
            disabled = False
        else:
            disabled = True
            
        with col2:
            if st.button("👁️ Detalhes", use_container_width=True, help="Selecione um item para visualizar!", disabled=disabled):
                categoria_id = df_categorias.loc[selected_row]['ID'].values[0]
                categoria = self.categoria_service.buscar_categoria_por_id(categoria_id)
                show_view_categoria_despesa(categoria)