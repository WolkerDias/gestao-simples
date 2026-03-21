# views/conta/list.py
import streamlit as st
import pandas as pd
from services.conta_service import ContaService
from views.conta.create import show_create_conta
from views.conta.view import show_view_conta

class ContaListView:
    def __init__(self):
        self.conta_service = ContaService()
        self.render()

    def render(self):
        st.title("🏦 Gestão de Contas")
        st.divider()
        
        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Conta", use_container_width=True):
                show_create_conta()

        # Preparar dados
        contas = self.conta_service.listar_contas()

        if not contas:
            st.info("Nenhuma conta cadastrada")
            return
        
        df_contas = pd.DataFrame([{
            'ID': conta.id, 
            'Nome': conta.nome, 
            'Tipo': conta.tipo,
            'Saldo Inicial': f'R$ {conta.saldo_inicial:.2f}'
        } for conta in contas])

        # Renderizar DataFrame com seleção
        conta_table = st.dataframe(
            df_contas,
            use_container_width=True,
            key="data_contas",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        selected_row = conta_table.selection.rows

        if selected_row:
            disabled = False
        else:
            disabled = True
            
        with col2:
            if st.button("👁️ Detalhes", use_container_width=True, help="Selecione um item para visualizar!", disabled=disabled):
                conta_id = df_contas.loc[selected_row]['ID'].values[0]
                conta = self.conta_service.buscar_conta_por_id(conta_id)
                show_view_conta(conta)