# views/estoque/inventario/encerrar_contagem_dialog.py
import streamlit as st
from datetime import datetime
from services.inventario_estoque_service import InventarioEstoqueService
from utils.message_handler import message_handler, MessageType
from utils.format import format_datetime
from streamlit_date_picker import date_picker, PickerType
from utils.validacoes import ValidationError

service = InventarioEstoqueService()

@st.dialog("Encerramento da Contagem", width="small")
def show_encerrar_contagem_dialog(inventario):
    with st.container(border=True):
        st.markdown(f"## Inventário: {inventario.referencia}")
        st.markdown(f"### Início da contagem: {format_datetime(inventario.data_inicio_contagem)}")
        st.markdown(f"### Total de itens: {len(inventario.itens)}")

        if len(inventario.itens) > 0:
            if inventario.data_fim_contagem:
                current_date = inventario.data_fim_contagem
                edit = 'Alterar'
                st.warning("Esta contagem já foi encerrada anteriormente.")
            else:
                current_date = datetime.now()
                edit = 'Encerrar'

            st.markdown("### Data/Hora do Encerramento")
            new_date = date_picker(
                picker_type=PickerType.time,
                value=current_date,
                key='encerramento_picker'
            )

            _, col2, col3 = st.columns([.4, .3, .3])
            with col2:
                if st.button(edit, type="primary", use_container_width=True):
                    try:
                        if new_date != "":
                            service.encerrar_contagem(inventario.id, new_date)
                            message_handler.add_message(
                                MessageType.SUCCESS,
                                f"Contagem encerrada em {format_datetime(new_date)}!"
                            )
                        else:
                            new_date = None
                            service.encerrar_contagem(inventario.id, new_date)
                            message_handler.add_message(
                                MessageType.SUCCESS,
                                f"Contagem reaberta!"
                            )
                        st.rerun()
                    except ValidationError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro inesperado: {str(e)}")
            
            with col3:
                if st.button("Cancelar", use_container_width=True):
                    st.rerun()

        # Se não houver itens, exibe mensagem
        else:
            st.warning("Não há itens para encerrar a contagem.")