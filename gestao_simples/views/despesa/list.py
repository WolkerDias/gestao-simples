# views/despesa/list.py
import streamlit as st
import pandas as pd
from services.despesa_service import DespesaService
from views.despesa.create import show_create_despesa
from views.despesa.view import show_view_despesa
from utils.message_handler import message_handler

class DespesaListView:
    def __init__(self):
        self.despesa_service = DespesaService()
        self.render()

    def render(self):
        st.title("💳 Gestão de Despesas")
        message_handler.display_toast_message()        

        # Filtros e controles
        col_filter, col_btn1, col_btn2 = st.columns([2, 1, 1], vertical_alignment="bottom")
        
        with col_filter:
            filtro_status = st.selectbox(
                "Filtrar por Status:",
                options=["Todas", "Pendentes", "Pagas"],
                help="Filtrar despesas por status de pagamento"
            )
        
        with col_btn1:
            if st.button("➕ Adicionar Despesa", use_container_width=True):
                show_create_despesa()

        # Preparar dados baseado no filtro
        if filtro_status == "Pendentes":
            despesas = self.despesa_service.listar_despesas_pendentes()
        else:
            despesas = self.despesa_service.listar_despesas()
            if filtro_status == "Pagas":
                despesas = [d for d in despesas if d.paga]

        if not despesas:
            st.info(f"Nenhuma despesa {filtro_status.lower()} encontrada")
            return
        
        df_despesas = pd.DataFrame([{
            'ID': d.id, 
            'Descrição': d.descricao, 
            'Valor': f'R$ {d.valor:.2f}',
            'Vencimento': d.data_vencimento.strftime('%d/%m/%Y'),
            'Pagamento': d.data_pagamento.strftime('%d/%m/%Y') if d.data_pagamento else '-',
            'Status': '✅ Paga' if d.paga else '⏳ Pendente',
            'Categoria': d.categoria.nome if d.categoria else '-',
            'Conta': d.conta.nome if d.conta else '-'
        } for d in despesas])

        # Aplicar coloração baseada no status
        def highlight_status(row):
            if row['Status'] == '✅ Paga':
                return ['background-color: #2F4F4F'] * len(row)
            elif row['Status'] == '⏳ Pendente':
                return ['background-color: #D2B48C'] * len(row)
            return [''] * len(row)

        # Renderizar DataFrame com seleção
        despesa_table = st.dataframe(
            df_despesas.style.apply(highlight_status, axis=1),
            use_container_width=True,
            key="data_despesas",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        selected_row = despesa_table.selection.rows

        if selected_row:
            disabled = False
            despesa_selecionada = despesas[selected_row[0]]
        else:
            disabled = True
            despesa_selecionada = None
            
        with col_btn2:
            if st.button("👁️ Detalhes", use_container_width=True, help="Selecione um item para visualizar!", disabled=disabled):
                despesa_id = df_despesas.loc[selected_row]['ID'].values[0]
                despesa = self.despesa_service.buscar_despesa_por_id(despesa_id)
                show_view_despesa(despesa)
        
        # Botão para marcar como paga (apenas para despesas pendentes)
        if not disabled and despesa_selecionada and not despesa_selecionada.paga:
            st.divider()
            col_pay = st.columns([3, 1])[1]
            with col_pay:
                if st.button("✅ Marcar como Paga", use_container_width=True, type="primary"):
                    try:
                        self.despesa_service.marcar_despesa_como_paga(despesa_selecionada.id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao marcar despesa como paga: {str(e)}")