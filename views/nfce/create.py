# views/nfce/create.py
import streamlit as st
from datetime import datetime
from models.nfce import NFCe
from services.nfce_service import NFCeService
from services.fornecedor_service import FornecedorService
from streamlit_date_picker import date_picker, PickerType
from utils.validacoes import ValidationError


@st.dialog("Novo NFCe", width="large")
def show_create_nfce():
    nfce_service = NFCeService()
    fornecedor_service = FornecedorService()
    fornecedores = fornecedor_service.listar_fornecedores()

    # Container para mensagens de erro/sucesso dentro do dialog
    status_container = st.empty()

    with st.form("novo_nfce", clear_on_submit=True):

        fornecedor = st.selectbox(
            "Selecione o Fornecedor", 
            options=[None]+fornecedores, 
            format_func=lambda f: f.nome if f else "Selecione...",
            index=0
        )
        chave_acesso = st.text_input("Chave de acesso")
        st.markdown("##### Data da emissão")
        data_emissao = date_picker(picker_type=PickerType.time, value=datetime.now(), key='date_picker')
        qrcode_url = st.text_input("QR Code")

        submitted = st.form_submit_button("Cadastrar")
        
        if submitted:
            try:
                if fornecedor is None:
                    st.error("Selecione um fornecedor válido.")
                else:
                    novo_nfce = NFCe(
                        fornecedor_id=fornecedor.id,
                        chave_acesso=chave_acesso, 
                        data_emissao=data_emissao, 
                        qrcode_url=qrcode_url,
                    )
                    created_nfce = nfce_service.criar_nfce(novo_nfce)

                    st.session_state.nova_nfce_id = created_nfce.id
                    st.rerun()

            except ValidationError as e:
                # Mostra todos os erros de validação no dialog
                with status_container:
                    for error in e.errors:
                        st.error(error)
                
            except Exception as e:
                # Mostra erro genérico no dialog
                with status_container:
                    st.error(f"Erro ao cadastrar NFCe: {str(e)}")