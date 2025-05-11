# views/fornecedor/create.py
import streamlit as st
from models.fornecedor import Fornecedor
from services.fornecedor_service import FornecedorService
from utils.validacoes import ValidationError
from utils.message_handler import message_handler, MessageType
from utils.format import clean_number

@st.dialog("Novo Fornecedor", width="large")
def show_create_fornecedor():
    fornecedor_service = FornecedorService()

    # Container para mensagens de erro/sucesso dentro do dialog
    status_container = st.empty()

    with st.form("novo_fornecedor"):
        nome = st.text_input("Nome do Fornecedor")
        cnpj = st.text_input("CNPJ")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")

        submitted = st.form_submit_button("Cadastrar")
        
        if submitted:
            try:
                novo_fornecedor = Fornecedor(
                    nome=nome, 
                    cnpj=clean_number(cnpj), 
                    email=email or None,
                    telefone=telefone or None
                )
                
                # Verificar se o fornecedor já existe no banco de dados
                if fornecedor_service.buscar_fornecedor_por_cnpj(cnpj):
                    # Mostra erro genérico no dialog
                    with status_container:
                        st.error(f"Fornecedor com CNPJ {cnpj} já cadastrado.")
                else:
                    # Tenta criar o fornecedor (inclui validações)
                    fornecedor_service.criar_fornecedor(novo_fornecedor)
                    
                    # Se chegou aqui, deu sucesso
                    message_handler.add_message(
                        MessageType.SUCCESS,
                        f"Fornecedor {nome} cadastrado com sucesso!"
                    )
                    
                    st.rerun()
                
            except ValidationError as e:
                # Mostra todos os erros de validação no dialog
                with status_container:
                    for error in e.errors:
                        st.error(error)
                
            except Exception as e:
                # Mostra erro genérico no dialog
                with status_container:
                    st.error(f"Erro ao cadastrar fornecedor: {str(e)}")