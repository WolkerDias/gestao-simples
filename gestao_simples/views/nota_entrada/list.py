# views/nota_entrada/list.py
import streamlit as st
import pandas as pd
from services.nota_entrada_service import NotaEntradaService
from services.fornecedor_service import FornecedorService
from views.nota_entrada.create import NotaEntradaCreateView
from views.nota_entrada.edit import NotaEntradaEditView
from views.nota_entrada.view import NotaEntradaDetailView
from views.nota_entrada.delete import confirm_delete_dialog
from utils.message_handler import message_handler
from utils.format import format_number, format_datetime, format_brl

class NotaEntradaListView:
    def __init__(self):
        self.nota_entrada_service = NotaEntradaService()
        self.fornecedor_service = FornecedorService()
        self.render()

    def render(self):
        
        if "create_mode" not in st.session_state:
            st.session_state.create_mode = False
        if "edit_mode" not in st.session_state:
            st.session_state.edit_mode = False
        if "view_mode" not in st.session_state:
            st.session_state.view_mode = False
            
            
        if st.session_state.create_mode:
            NotaEntradaCreateView()
        elif st.session_state.edit_mode:
            NotaEntradaEditView(st.session_state.selected_nota_entrada_id)
        elif st.session_state.view_mode:
            NotaEntradaDetailView(st.session_state.selected_nota_entrada_id)
        else:
            self._render_nota_entrada_table()
    
    def _render_nota_entrada_table(self):
        st.title("📦 Gestão de Entradas")
        message_handler.display_toast_message()
        # Resetar estado ao renderizar a tabela
        if 'temp_items' in st.session_state:
            del st.session_state.temp_items

        col1, col2, col3, col4 = st.columns(4)

        disabled = False

        if col1.button("➕ Nova Entrada", use_container_width=True):
            st.session_state.create_mode = True
            st.rerun()
        notas_entrada = self.nota_entrada_service.listar_notas_entrada()
        fornecedores = self.fornecedor_service.listar_fornecedores()
        
        if not notas_entrada:
            st.info("Nenhuma Nota de Entrada cadastrada")
            return
            
        df = pd.DataFrame([{
            'ID': n.id,
            'Data da emissão': format_datetime(n.data_emissao),
            'Fornecedor': next((f.nome for f in fornecedores if f.id == n.fornecedor_id), 'Desconhecido'),
            'Número': format_number(n.numero_nota_entrada),
            'Total': format_brl(n.total_nota_entrada),
            'URL': n.url
        } for n in notas_entrada])
        
        # Renderizar DataFrame com seleção
        nota_entrada = st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "URL": st.column_config.LinkColumn("URL"),
                "ID": st.column_config.Column("ID", width="small")
            },
            key="data",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )

        selected_row = nota_entrada.selection.rows
        
        if selected_row:
            nota_entrada_id = df.loc[selected_row]['ID'].values[0]
            disabled = False
        else:
            disabled = True
            
        with col2:
            if st.button("👁️ Detalhes", use_container_width=True, disabled=disabled):
                st.session_state.view_mode = True
                st.session_state.selected_nota_entrada_id = nota_entrada_id
                st.rerun()
        with col3:
            if st.button("✏️ Editar", use_container_width=True, disabled=disabled):
                st.session_state.edit_mode = True
                st.session_state.selected_nota_entrada_id = nota_entrada_id
                st.rerun()
        with col4:
            if st.button("🗑️ Excluir", use_container_width=True, disabled=disabled):
                confirm_delete_dialog(nota_entrada_id, self.nota_entrada_service)