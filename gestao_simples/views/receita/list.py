# views/receita/list.py
import streamlit as st
import pandas as pd
from services.receita_service import ReceitaService
from views.receita.create import show_create_receita
from views.receita.view import show_view_receita
from utils.message_handler import message_handler

class ReceitaListView:
    def __init__(self):
        self.receita_service = ReceitaService()
        self.render()

    def render(self):
        st.title("💰 Gestão de Receitas")
        message_handler.display_toast_message()        

        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Receita", use_container_width=True):
                show_create_receita()

        # Preparar dados
        receitas = self.receita_service.listar_receitas()

        if not receitas:
            st.info("Nenhuma receita cadastrada")
            return
        
        df_receitas = pd.DataFrame([{
            'ID': r.id, 
            'Descrição': r.descricao, 
            'Valor': f'R$ {r.valor:.2f}',
            'Data Recebimento': r.data_recebimento.strftime('%d/%m/%Y'),
            'Categoria': r.categoria.nome if r.categoria else '-',
            'Conta': r.conta.nome if r.conta else '-'
        } for r in receitas])

        # Renderizar DataFrame com seleção
        receita_table = st.dataframe(
            df_receitas,
            use_container_width=True,
            key="data_receitas",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        selected_row = receita_table.selection.rows

        if selected_row:
            disabled = False
        else:
            disabled = True
            
        with col2:
            if st.button("👁️ Detalhes", use_container_width=True, help="Selecione um item para visualizar!", disabled=disabled):
                receita_id = df_receitas.loc[selected_row]['ID'].values[0]
                receita = self.receita_service.buscar_receita_por_id(receita_id)
                show_view_receita(receita)