# views/estoque/inventario/create.py
import streamlit as st
from services.inventario_estoque_service import InventarioEstoqueService
from models.inventario_estoque import InventarioEstoque
from utils.validacoes import ValidationError
from streamlit_date_picker import date_picker, PickerType
from datetime import datetime

inventario_service = InventarioEstoqueService()

@st.dialog("Novo Inventário", width="large")
def show_create_inventario():
    with st.form("novo_inventario_form"):
        st.subheader("Cadastro de Novo Inventário")
        
        referencia = st.text_input(
            "Referência (MM/AAAA)", 
            placeholder="04/2025",
            max_chars=7, 
            value=datetime.now().strftime("%m/%Y"))

        st.markdown("Início da contagem:")
        data_inicio_contagem = date_picker(
            picker_type=PickerType.time, 
            value=datetime.now(), 
            key='create_inicio')

        observacoes = st.text_area("Observações", "")
        
        submit_btn = st.form_submit_button("Cadastrar", icon=":material/add:")
        
        if submit_btn:
            try:
                novo_inventario = InventarioEstoque(
                    referencia=referencia,
                    data_inicio_contagem=data_inicio_contagem,
                    observacoes=observacoes
                )
                
                # Cria novo inventário
                inventario = inventario_service.criar_inventario(novo_inventario)
                
                # Armazena o ID do inventário para abrir a edição depois
                st.session_state.novo_inventario_id = inventario.id
                st.session_state.abrir_editor = True
                
                # Feedback de sucesso
                st.success("Inventário criado com sucesso!")
                
                # Força o rerun para fechar este diálogo
                st.rerun()
                
            except ValidationError as e:
                st.error(e)
            except Exception as e:
                st.error(f"Erro ao cadastrar inventário: {str(e)}")