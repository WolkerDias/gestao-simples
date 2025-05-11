# views/produto/associacao/editar_associacao.py
import streamlit as st
from services.produto_fornecedor_associacao_service import ProdutoFornecedorAssociacaoService
from services.produto_service import ProdutoService
from utils.message_handler import message_handler, MessageType

produto_service = ProdutoService()

@st.dialog("✏️ Editar Associação", width="large")
def show_view_associacao(associacao):
    service = ProdutoFornecedorAssociacaoService()

    with st.form(key='editar_associacao_form', border=True):
        st.markdown(f"**Fornecedor: {associacao.fornecedor_id} - {associacao.fornecedor_nome}**")
        st.markdown(f"**Item do fornecedor: {associacao.codigo_produto_fornecedor} | {associacao.descricao_produto_fornecedor} | {associacao.unidade_medida}**")

        st.divider()
        st.subheader("🔗 Associar a Produto")
        col1, col2 = st.columns([0.7, 0.3])
        produtos = produto_service.listar_produtos()
        produto_selecionado = col1.selectbox(
            "Produto Padrão",
            options=produtos,
            index=[p.id for p in produtos].index(associacao.produto_id),
            format_func=lambda p: f"{p.id} - {p.nome}"
        )

        quantidade = col2.number_input(
            "Quantidade por Grade",
            min_value=0.01,
            value=float(associacao.quantidade_por_grade),
            step=0.01,
            format="%.3f"
        )

        if col2.form_submit_button("Salvar Alterações", use_container_width=True):
            dados = {
                'produto_id': produto_selecionado.id,
                'quantidade_por_grade': quantidade
            }
            try:            
                service.atualizar_associacao(associacao.id, dados)
                message_handler.add_message(
                    MessageType.SUCCESS,
                    f"Associação atualizada com sucesso!"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar Associação: {e}")                 