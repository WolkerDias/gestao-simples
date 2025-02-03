# views/fornecedor/list.py
import streamlit as st
import pandas as pd
from services.fornecedor_service import FornecedorService
from services.fornecedor_service import FornecedorService
from views.fornecedor.create import show_create_fornecedor
from views.fornecedor.view import show_view_fornecedor
from utils.message_handler import message_handler

class FornecedorListView:
    def __init__(self):
        self.fornecedor_service = FornecedorService()
        self.render()

    def render(self):
        st.title("📦 Gestão de Fornecedores")
        message_handler.display_toast_message()        
        
        # Preparar dados
        fornecedores = self.fornecedor_service.listar_fornecedores()
        df_fornecedores = pd.DataFrame([{
            'ID': f.id, 
            'Nome': f.nome, 
            'CNPJ': f.cnpj, 
            'E-mail': f.email,
            'Telefone': f.telefone
        } for f in fornecedores])


        # Renderizar DataFrame com seleção
        fornecedor = st.dataframe(
            df_fornecedores,
            use_container_width=True,
            key="data",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
        )
        
        selected_row = fornecedor.selection.rows

        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Fornecedor", use_container_width=True):
                show_create_fornecedor()

        if selected_row:
            with col2:
                if st.button("👁️ Visualizar Fornecedor", use_container_width=True):
                    fornecedor_id = df_fornecedores.loc[selected_row]['ID'].values[0]
                    fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(fornecedor_id)
                    show_view_fornecedor(fornecedor)

        # Verificar se há uma nova Fornecedor para abrir a visualização
        if 'nova_fornecedor_id' in st.session_state:
            fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(st.session_state.nova_fornecedor_id)
            show_view_fornecedor(fornecedor)
            del st.session_state.nova_fornecedor_id

