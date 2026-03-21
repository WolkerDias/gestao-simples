# views/categoria_receita/list.py
import streamlit as st
import pandas as pd
from services.categoria_receita_service import CategoriaReceitaService
from views.categoria_receita.create import show_create_categoria_receita
from views.categoria_receita.view import show_view_categoria_receita

class CategoriaReceitaListView:
    def __init__(self):
        self.categoria_service = CategoriaReceitaService()
        self.render()

    def render(self):
        st.title("🏷️ Categorias de Receita")
        st.divider()
        
        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Categoria", use_container_width=True):
                show_create_categoria_receita()

        # Preparar dados
        categorias = self.categoria_service.listar_categorias()

        if not categorias:
            st.info("Nenhuma categoria cadastrada")
            return
        
        df_categorias = pd.DataFrame([{
            'ID': cat.id, 
            'Nome': cat.nome, 
            'Descrição': cat.descricao if cat.descricao else '-',
            'Qtd. Receitas': len(cat.receitas) if hasattr(cat, 'receitas') else 0
        } for cat in categorias])

        # Renderizar DataFrame com seleção
        categoria_table = st.dataframe(
            df_categorias,
            use_container_width=True,
            key="data_categorias",
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
                show_view_categoria_receita(categoria)