# views/fornecedor/list.py
import streamlit as st
import pandas as pd
from services.fornecedor_service import FornecedorService
from views.fornecedor.create import show_create_fornecedor
from views.fornecedor.view import show_view_fornecedor
from utils.format import format_cnpj
from utils.message_handler import message_handler
from services.auth_service import AuthService

class FornecedorListView:
    def __init__(self):
        self.fornecedor_service = FornecedorService()
        self.auth_service = AuthService()
        self.render()

    def render(self):
        st.title("📦 Gestão de Fornecedores")
        message_handler.display_toast_message()        

        # Botões de ação
        col1, col2 = st.columns([2, 2])
        
        with col1:
            if st.button("➕ Adicionar Fornecedor", use_container_width=True):
                show_create_fornecedor()

        # Preparar dados
        fornecedores = self.fornecedor_service.listar_fornecedores()

        if not fornecedores:
            st.info("Nenhum fornecedor cadastrado")
            return
        
        df_fornecedores = pd.DataFrame([{
            'ID': f.id, 
            'Nome': f.nome, 
            'CNPJ': format_cnpj(f.cnpj), 
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

        if selected_row:
            disabled = False
        else:
            disabled = True
            
        with col2:
            if st.button("👁️ Detalhes", use_container_width=True, help="Selecione um item para visualizar!", disabled=disabled):
                fornecedor_id = df_fornecedores.loc[selected_row]['ID'].values[0]
                fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(fornecedor_id)
                show_view_fornecedor(fornecedor)

        # Verificar se há um novo Fornecedor para abrir a visualização
        if 'nova_fornecedor_id' in st.session_state:
            fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(st.session_state.nova_fornecedor_id)
            show_view_fornecedor(fornecedor)
            del st.session_state.nova_fornecedor_id

