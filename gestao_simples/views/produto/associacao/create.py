# views/produto/associacao/create.py
import streamlit as st
from services.produto_fornecedor_associacao_service import ProdutoFornecedorAssociacaoService
from services.produto_service import ProdutoService
from utils.message_handler import message_handler, MessageType

service = ProdutoFornecedorAssociacaoService()
produto_service = ProdutoService()

@st.dialog("📥 Fila de Associação de Produtos", width="large")
def show_create_associacao():
    # Recarrega a lista ao iniciar/recarregar a página
    if 'itens_fila' not in st.session_state:
        st.session_state.itens_fila = service.listar_todos_itens_nao_associados()

    if 'indice_atual' not in st.session_state:
        st.session_state.indice_atual = 0

    if 'form_id' not in st.session_state:
        st.session_state.form_id = 0

    if not st.session_state.itens_fila:
        message_handler.add_message(
            MessageType.SUCCESS,
            f"Todos os itens foram associados! 🎉"
        )        
        st.rerun()
        return

    item_atual = st.session_state.itens_fila[st.session_state.indice_atual]
    produtos = produto_service.listar_produtos()

    # Card do Item
    with st.form(key=f"associar_form_{st.session_state.form_id}", border=True):
        st.markdown(f"**Fornecedor: {item_atual['fornecedor_id']} - {item_atual['fornecedor_nome']}**")
        st.markdown(f"**Item do fornecedor: {item_atual['codigo_produto_fornecedor']} | {item_atual['descricao']} | {item_atual['unidade']}**")

        st.divider()
        st.subheader("🔗 Associar a Produto")
        col1, col2 = st.columns([0.7, 0.3])

        produto_selecionado = col1.selectbox(
            "Produto Padrão",
            key=f"produto_selecionado_{st.session_state.form_id}",
            placeholder="Selecione um produto",
            options=produtos,
            format_func=lambda p: f"{p.id} - {p.nome} - {p.unidade_medida}",
            index=None
        )

        quantidade = col2.number_input(
            "Quantidade por Grade",
            key=f"quantidade_{st.session_state.form_id}",
            min_value=0.01, 
            step=0.01, 
            value=1.0, 
            format="%.3f"
        )

        if st.form_submit_button("Salvar Associação", use_container_width=True):
            if produto_selecionado is None:
                st.error("Selecione um produto para associar.")
            else:
                _salvar_associacao(item_atual, produto_selecionado.id, quantidade)

    # Controles de Navegação
    col_controls = st.columns([0.33333, 0.33333, 0.33333], vertical_alignment="center")

    if col_controls[0].button("⏮️ Item Anterior", disabled=st.session_state.indice_atual == 0, use_container_width=True):
        _retroceder_item()

    col_controls[1].button(f"**Item {st.session_state.indice_atual + 1} de {len(st.session_state.itens_fila)}**", use_container_width=True, type="tertiary")

    if col_controls[2].button("Próximo Item ⏭️", disabled=st.session_state.indice_atual == len(st.session_state.itens_fila) - 1, use_container_width=True):
        _avancar_item()

def _salvar_associacao(item, produto_id, quantidade):
    dados = {
        'produto_id': produto_id,
        'fornecedor_id': item['fornecedor_id'],
        'quantidade_por_grade': quantidade,
        'codigo_produto_fornecedor': item['codigo_produto_fornecedor'],
        'descricao_produto_fornecedor': item['descricao']
    }

    service.criar_associacao(dados)
    st.session_state.itens_fila.pop(st.session_state.indice_atual)

    # Atualiza a lista e reinicia o processo
    st.session_state.itens_fila = service.listar_todos_itens_nao_associados()
    st.session_state.form_id += 1
    st.rerun(scope="fragment")

def _avancar_item():
    if st.session_state.indice_atual < len(st.session_state.itens_fila) - 1:
        st.session_state.indice_atual += 1
        st.session_state.form_id += 1
    st.rerun(scope="fragment")

def _retroceder_item():
    if st.session_state.indice_atual > 0:
        st.session_state.indice_atual -= 1
        st.session_state.form_id += 1
    st.rerun(scope="fragment")
