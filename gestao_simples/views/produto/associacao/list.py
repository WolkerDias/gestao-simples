# views/produto/associacao/list.py
import streamlit as st
import pandas as pd
from services.produto_fornecedor_associacao_service import ProdutoFornecedorAssociacaoService
from views.produto.associacao.view import show_view_associacao
from views.produto.associacao.create import show_create_associacao
from views.produto.associacao.delete import confirm_delete_dialog
from utils.format import format_datetime
from utils.message_handler import message_handler

class AssociacoesListView:
    def __init__(self):
        self.service = ProdutoFornecedorAssociacaoService()
        self.render()

    def render(self):
        st.title("📋 Associações Cadastradas")
        with st.spinner("🔍 Buscando itens não associados..."):        
            itens_nao_associados = self.service.listar_todos_itens_nao_associados()

        if itens_nao_associados:
            st.info(f"⛓️‍💥 Produtos não associados encontrados: {len(itens_nao_associados)}")
            disabled = False
        else:
            disabled = True

        #st.dataframe(pd.DataFrame(itens_nao_associados))

        message_handler.display_toast_message()        

        # Botões de ação
        columns = st.columns([2, 2, 2, 2], vertical_alignment="center")

        with columns[0]:
            if st.button("🔄 Atualizar Lista", use_container_width=True):
                st.rerun()        
        
        with columns[1]:
            if st.button("🔗 Associar Produtos", use_container_width=True, disabled=disabled):
                show_create_associacao(itens_nao_associados)        

        with st.spinner("📦 Carregando associações existentes..."):
            associacoes = self.service.listar_associacoes()
            
        if not associacoes:
            st.info("Nenhuma associação cadastrada.")
            return

        df = pd.DataFrame([{
            'ID': a.id,
            'Data': format_datetime(a.created_at),
            'Fornecedor': a.fornecedor.nome,
            'Ref. Fornecedor': a.codigo_produto_fornecedor,
            'Produto': a.produto.nome,
            'Unidade': a.produto.unidade_medida,
            'Descrição Fornecedor': a.descricao_produto_fornecedor,
            'Qtd. Grade': a.quantidade_por_grade
        } for a in associacoes])

        associacao = st.dataframe(
            df,
            use_container_width=True,
            key="data",
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                'Qtd. Grade': st.column_config.NumberColumn(format="%.3f"),
            },
            hide_index=True,
        )

        selected_row = associacao.selection.rows

        if selected_row:
            disabled = False
        else:
            disabled = True

        with columns[2]:
            if st.button("✏️ Editar Associação", use_container_width=True, help="Selecione um item para editar!", disabled=disabled):
                associacao_id = df.loc[selected_row]['ID'].values[0]
                associacao = self.service.buscar_associacao_por_id(associacao_id)
                associacao.fornecedor_nome = df.loc[selected_row]['Fornecedor'].values[0]
                associacao.unidade_medida = df.loc[selected_row]['Unidade'].values[0]
                show_view_associacao(associacao)
        
        with columns[3]:
            if st.button("🗑️ Excluir Associação", use_container_width=True, help="Selecione um item para excluir!", disabled=disabled):
                associacao_id = df.loc[selected_row]['ID'].values[0]
                confirm_delete_dialog(associacao_id, self.service)