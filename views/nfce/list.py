# views/nfce/list.py
import streamlit as st
import pandas as pd
from services.nfce_service import NFCeService
from services.fornecedor_service import FornecedorService
from views.nfce.create import show_create_nfce
from views.nfce.view import show_view_nfce
from utils.message_handler import message_handler


class NFCeListView:
    def __init__(self):
        self.nfce_service = NFCeService()
        self.fornecedor_service = FornecedorService()
        self.render()

    def render(self):
        st.title("📦 Gestão de NFCes")
        message_handler.display_toast_message()
        
        # Preparar dados
        nfces = self.nfce_service.listar_nfces()
        fornecedores = self.fornecedor_service.listar_fornecedores()

        df_nfces = pd.DataFrame([{
            'ID': n.id, 
            'Chave de acesso': n.chave_acesso, 
            'Data da emissão': pd.to_datetime(n.data_emissao).strftime("%d/%m/%Y %H:%M:%S"), 
            'QR Code': n.qrcode_url,
            'Fornecedor': next((f.nome for f in fornecedores if f.id == n.fornecedor_id), 'Desconhecido')
        } for n in nfces])

        # Renderizar DataFrame com seleção
        nfce = st.dataframe(
            df_nfces,
            use_container_width=True,
            key="data",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            column_config={
                "QR Code": st.column_config.LinkColumn("QR Code"),
            },
        )
        
        selected_row = nfce.selection.rows

        # Botões de ação
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("➕ Adicionar NFCe", use_container_width=True):
                show_create_nfce()

        if selected_row:
            with col2:
                if st.button("👁️ Visualizar NFCe", use_container_width=True):
                    nfce_id = df_nfces.loc[selected_row]['ID'].values[0]
                    nfce = self.nfce_service.buscar_nfce_por_id(nfce_id)
                    show_view_nfce(nfce)

        # Verificar se há uma nova NFCe para abrir a visualização
        if 'nova_nfce_id' in st.session_state:
            nfce = self.nfce_service.buscar_nfce_por_id(st.session_state.nova_nfce_id)
            show_view_nfce(nfce)
            del st.session_state.nova_nfce_id