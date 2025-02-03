# views/fornecedor/view.py
import streamlit as st
from services.fornecedor_service import FornecedorService

@st.dialog("Visualizar Fornecedor", width="large")
def show_view_fornecedor(fornecedor):
    fornecedor_service = FornecedorService()
    
    # Tabs para diferentes funcionalidades
    tab_view, tab_edit = st.tabs(["Visualizar", "Editar"])
    
    # Tab de Visualização
    with tab_view:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Fornecedor:**")
            st.code(fornecedor.nome, language=None)
            st.write(f"**E-mail:**")
            st.code(fornecedor.email, language=None)
        
        with col2:
            st.write("**CNPJ:**")
            st.code(fornecedor.cnpj, language=None)
            st.write("**Telefone:**")
            st.code(fornecedor.telefone, language=None)

        # Botão de excluir na aba de visualização
        with st.expander("🗑️ Excluir Fornecedor"):
            if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                try:
                    fornecedor_service.deletar_fornecedor(fornecedor.id)
                    st.success(f"Fornecedor excluído com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir Fornecedor: {e}")

    # Tab de Edição
    with tab_edit:
        with st.form("editar_fornecedor"):
            nome = st.text_input("Nome do Fornecedor", value=fornecedor.nome)
            cnpj = st.text_input("CNPJ", value=fornecedor.cnpj)
            email = st.text_input("E-mail", value=fornecedor.email)
            telefone = st.text_input("Telefone", value=fornecedor.telefone)

            submitted = st.form_submit_button("Atualizar")
            
            if submitted:
                fornecedor.nome = nome
                fornecedor.cnpj = cnpj
                fornecedor.email = email
                fornecedor.telefone = telefone
                
                fornecedor_service.atualizar_fornecedor(fornecedor)
                st.success("Fornecedor atualizado com sucesso!")
                st.rerun()