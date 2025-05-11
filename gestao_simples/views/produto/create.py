# views/produto/create.py
import streamlit as st
from models.produto import Produto
from services.produto_service import ProdutoService
from utils.validacoes import ValidationError
from utils.message_handler import message_handler, MessageType
from utils.format import padronizar_texto

@st.dialog("Novo Produto", width="large")
def show_create_produto():
    produto_service = ProdutoService()

    # Container para mensagens de erro/sucesso dentro do dialog
    status_container = st.empty()

    with st.form("novo_produto"):
        col1, col2 = st.columns([2, 1])
        with col1:
            nome = st.text_input(
                label="Nome do produto*",
                placeholder="Ex: açúcar cristal",  # Exemplo formatado
                help="⚠️ O texto será salvo em minúsculas, sem espaços extras no início/fim e com apenas um espaço entre palavras."  # Mensagem de ajuda
                )   
        
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
                help="Selecione a unidade de medida do produto."
            )

        descricao = st.text_area("Descrição do Produto", max_chars=255)

        submitted = st.form_submit_button("Cadastrar")
        
        if submitted:
            try:
                # Padroniza o nome do produto antes de salvar
                nome = padronizar_texto(nome)
                
                # Verificar se o produto já existe no banco de dados
                if produto_service.buscar_produto_por_nome(nome):
                    # Mostra erro genérico no dialog
                    with status_container:
                        st.error(f"Produto com nome {nome} já cadastrado.")
                else:
                    novo_produto = Produto(
                        nome=nome, 
                        descricao=descricao, 
                        unidade_medida=unidade_medida
                    )
                    # Tenta criar o produto (inclui validações)
                    produto_service.criar_produto(novo_produto)
                    
                    # Se chegou aqui, deu sucesso
                    message_handler.add_message(
                        MessageType.SUCCESS,
                        f"Produto {nome} cadastrado com sucesso!"
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
                    st.error(f"Erro ao cadastrar produto: {str(e)}")