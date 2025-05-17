# views/produto/view.py
import streamlit as st
from services.produto_service import ProdutoService
from utils.format import padronizar_texto
from utils.validacoes import ValidationError
from utils.message_handler import message_handler, MessageType

@st.dialog("Visualizar Produto", width="large")
def show_view_produto(produto):
    produto_service = ProdutoService()
    
    # Tabs para diferentes funcionalidades
    tab_view, tab_edit = st.tabs(["Visualizar", "Editar"])
    
    # Tab de Visualização
    with tab_view:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"Nome do produto")
            st.code(produto.nome, language=None)
        
        with col2:
            st.write("Unidade de medida")
            st.code(produto.unidade_medida, language=None)
        
        st.write("Descrição do produto")
        st.code(produto.descricao, language=None, height=130)


        # Botão de excluir na aba de visualização
        with st.popover("🗑️ Excluir Produto", use_container_width=True):
            st.warning("⚠️ Você tem certeza que deseja excluir este produto? Esta ação não pode ser desfeita.")
            if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                
                try:
                    produto_service.deletar_produto(produto.id)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir Produto: {e}")

    # Tab de Edição
    with tab_edit:
        with st.form("editar_produto"):
            col1, col2 = st.columns([2, 1])
            with col1:
                nome = st.text_input(
                    value=produto.nome,
                    label="Nome do produto*",
                    placeholder="Ex: açúcar cristal",  # Exemplo formatado
                    help="⚠️ O texto será salvo em minúsculas, sem espaços extras no início/fim e com apenas um espaço entre palavras.")  # Mensagem de ajuda

            with col2:
                unidades = {
                    "kg": "Quilograma (kg)",
                    "g": "Grama (g)",
                    "l": "Litro (l)",
                    "ml": "Mililitro (ml)",
                    "un": "Unidade (un)",
                    "pc": "Peça (pc)",
                    "cx": "Caixa (cx)",
                    "m": "Metro (m)"
                }  

                unidade_medida = st.selectbox(
                    label="Unidade de Medida",
                    options=list(unidades.keys()),
                    format_func=lambda x: unidades[x],
                    help="Selecione a unidade de medida do produto.",
                    index=list(unidades.keys()).index(produto.unidade_medida) if produto.unidade_medida in unidades else 0
                )       

            descricao = st.text_area("Descrição", max_chars=255, height=130, value=produto.descricao)

            submitted = st.form_submit_button("Atualizar")

            if submitted:
                try:
                    # Padroniza o nome do produto antes de salvar
                    nome = padronizar_texto(nome)
                    
                    # Verificar se o produto já existe no banco de dados
                    produto_existente = produto_service.buscar_produto_por_nome(nome)
                    if produto_existente and produto_existente.id != produto.id:
                        # Se o produto existente não é o mesmo que está sendo atualizado, mostra erro
                        st.error(f"Produto com nome {nome} já cadastrado com id {produto_existente.id}.")
                    else:
                        produto.nome = nome
                        produto.descricao = descricao
                        produto.unidade_medida = unidade_medida

                        # Tenta atualizar o produto
                        produto_service.atualizar_produto(produto)
                        
                        # Se chegou aqui, deu sucesso
                        message_handler.add_message(
                            MessageType.SUCCESS,
                            f"Produto {nome} atualizado com sucesso!"
                        )
                        
                        st.rerun()
                    
                except ValidationError as e:
                    # Mostra todos os erros de validação no dialog
                    for error in e.errors:
                        st.error(error)
                    
                except Exception as e:
                    # Mostra erro genérico no dialog
                    st.error(f"Erro ao cadastrar produto: {str(e)}")