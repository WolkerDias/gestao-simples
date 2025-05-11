# views/estoque/inventario/list.py
import streamlit as st
import pandas as pd
from services.inventario_estoque_service import InventarioEstoqueService
from views.estoque.inventario.create import show_create_inventario
from views.estoque.inventario.edit import show_edit_inventario
from utils.format import format_datetime
from utils.message_handler import message_handler
from views.estoque.inventario.delete import confirm_delete_dialog
from views.estoque.inventario.encerrar_contagem import show_encerrar_contagem_dialog

class InventarioListView:
    def __init__(self):
        self.service = InventarioEstoqueService()
        self.render()

    def render(self):
        st.title("📋 Inventários de Estoque Registrados")
        message_handler.display_toast_message()

        # Verificar se há inventário recém-criado para abrir editor
        if 'novo_inventario_id' in st.session_state and 'abrir_editor' in st.session_state and st.session_state.abrir_editor:
            inventario_id = st.session_state.novo_inventario_id
            inventario = self.service.buscar_inventario_por_id(inventario_id)
            
            if inventario:
                # Limpa o flag antes de mostrar o diálogo para evitar loops
                st.session_state.abrir_editor = False
                
                # Abre o editor automaticamente
                show_edit_inventario(inventario)

        # Botões de ação
        columns = st.columns([2, 2, 2, 2, 2], vertical_alignment="center")

        with columns[0]:
            if st.button("🔄 Atualizar Lista", use_container_width=True):
                # Limpa todas as flags ao atualizar
                if 'abrir_editor' in st.session_state:
                    st.session_state.abrir_editor = False
                st.rerun()

        with columns[1]:
            if st.button("📥 Novo Inventário", use_container_width=True):
                show_create_inventario()

        # Listagem dos inventários
        inventarios = self.service.listar_inventarios()

        if not inventarios:
            st.info("Nenhum inventário registrado.")
            return

        # Cria DataFrame com os inventários
        df = pd.DataFrame([{
            'ID': inv.id,
            'Referência': inv.referencia,
            'Início': format_datetime(inv.data_inicio_contagem),
            'Fim': format_datetime(inv.data_fim_contagem),
            'Observações': inv.observacoes,
            'Qtd. Itens': len(inv.itens)
        } for inv in inventarios])

        # Exibe a tabela
        selected_inventario = st.dataframe(
            df,
            use_container_width=True,
            key="data_inventario",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            column_config={
                "Referência": st.column_config.Column(width="medium"),
                "Qtd. Itens": st.column_config.NumberColumn(width="small")
            }
        )

        # Inicializa o estado para seleção persistente se não existir
        if 'selected_inventario_id' not in st.session_state:
            st.session_state.selected_inventario_id = None

        # Lógica para manter seleção após atualizações
        selected_row = selected_inventario.selection.rows

        if selected_row:
            # Se uma linha foi selecionada pelo usuário, atualiza o estado
            inventario_id = df.loc[selected_row]['ID'].values[0]
            inventario_referencia = df.loc[selected_row]['Referência'].values[0]
            st.session_state.selected_inventario_id = inventario_id
            st.session_state.selected_inventario_referencia = inventario_referencia
            disabled = False
        elif st.session_state.selected_inventario_id is not None:
            # Se não há seleção atual, mas havia uma anteriormente armazenada
            inventario_id = st.session_state.selected_inventario_id
            inventario_referencia = st.session_state.selected_inventario_referencia
            disabled = False
        else:
            # Nenhuma seleção atual ou anterior
            disabled = True

        with columns[2]:
            if st.button("👁️ Detalhes", use_container_width=True, disabled=disabled, help="Selecione um item para ver detalhes"):
                inventario = self.service.buscar_inventario_por_id(inventario_id)
                show_edit_inventario(inventario)

        with columns[3]:
            if st.button("⏹️ Encerrar Contagem", disabled=disabled, use_container_width=True, help="Selecione um item para encerrar a contagem"):
                inventario = self.service.buscar_inventario_por_id(inventario_id)

                show_encerrar_contagem_dialog(inventario)
                
        with columns[4]:
            if st.button("🗑️ Excluir", use_container_width=True, disabled=disabled, help="Selecione um item para ver excluir"):
                confirm_delete_dialog(inventario_id, inventario_referencia, self.service)