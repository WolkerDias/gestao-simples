# views/estoque/inventario/edit.py
import streamlit as st
from services.inventario_estoque_service import InventarioEstoqueService
from services.produto_service import ProdutoService
from models.inventario_estoque import InventarioEstoque
from utils.validacoes import ValidationError
from streamlit_date_picker import date_picker, PickerType
from utils.message_handler import message_handler, MessageType
from utils.format import format_datetime, format_decimal

inventario_service = InventarioEstoqueService()
produto_service = ProdutoService()

@st.dialog("Gerenciar Inventário", width="large")
def show_edit_inventario(inventario: InventarioEstoque = None):
    # Verifica se o inventário está encerrado
    inventario_encerrado = inventario.data_fim_contagem is not None    
    
    # Inicialização dos estados para edição
    if 'itens_temporarios' not in st.session_state:
        st.session_state.itens_temporarios = [{
            "id": item.id,
            "id_produto": item.produto.id, 
            "produto": item.produto.nome,
            "quantidade": item.quantidade_contada,
            "unidade": item.produto.unidade_medida
        } for item in inventario.itens]
    
    # Sempre armazena o ID do inventário atual
    st.session_state.inventario_id = inventario.id

    # Armazena também como selected_inventario_id para manter a seleção na tabela
    st.session_state.selected_inventario_id = inventario.id
    st.session_state.selected_inventario_referencia = inventario.referencia    

    # Título do expander com status
    status = "🔴 ENCERRADO" if inventario_encerrado else "🟢 EM ANDAMENTO"
    
    # Título do expander com informações do inventário
    expander_title = f"## {status} \n***Inventário: {inventario.referencia} - iniciado em {format_datetime(inventario.data_inicio_contagem)}***"

    # Mostra mensagem se estiver encerrado
    if inventario_encerrado:
        st.warning(f"Inventário encerrado em {format_datetime(inventario.data_fim_contagem)}. Edições desabilitadas.")

    with st.expander(expander_title, expanded=False):
        with st.form("editar_inventario_form"):
            referencia = st.text_input(
                "Referência (MM/AAAA)", 
                value=inventario.referencia,
                placeholder="04/2025",
                max_chars=7,
                disabled=inventario_encerrado
                )

            if not inventario_encerrado:
                st.markdown("Início da contagem:")
                data_inicio_contagem = date_picker(
                    picker_type=PickerType.time, 
                    value=inventario.data_inicio_contagem, 
                    key='edit_inicio')

            observacoes = st.text_area("Observações", value=inventario.observacoes, disabled=inventario_encerrado)

            submit_btn = st.form_submit_button("Atualizar", icon=":material/update:", disabled=inventario_encerrado)
            
            if submit_btn:
                try:
                    dados_atualizados = InventarioEstoque(
                        referencia=referencia,
                        data_inicio_contagem=data_inicio_contagem,
                        observacoes=observacoes
                    )
                    
                    # Atualiza o inventário
                    inventario_service.atualizar_inventario(inventario.id, dados_atualizados)
                    message_handler.add_message(
                        MessageType.SUCCESS,
                        f"Inventário atualizado com sucesso!"
                    )
                    st.rerun()
                    
                except ValidationError as e:
                    st.error(e)
                except Exception as e:
                    st.error(f"Erro ao atualizar inventário: {str(e)}")

    # Se o inventário estiver encerrado, não permite adicionar novos itens
    if not inventario_encerrado:
        with st.expander("**Adicionar Itens ao Inventário**", expanded=True, icon=":material/add:"):
            produtos = produto_service.listar_produtos()
            col1, col2, col3 = st.columns([.6, .2, .2], vertical_alignment="bottom")
            
            with col1:
                # Filtra produtos não adicionados
                produtos_nao_adicionados = [
                    p for p in produtos 
                    if p.id not in {
                        item.get("id_produto", None)  # Usar .get() para evitar KeyError
                        for item in st.session_state.itens_temporarios
                    }
                ]
                
                produto = st.selectbox(
                    "Produto", 
                    produtos_nao_adicionados,  # Mostra apenas produtos não adicionados
                    placeholder="Selecione um produto",
                    key="produto_selecionado",
                    index=None,
                    format_func=lambda p: f"{p.nome} ({p.unidade_medida})"
                )
            
            with col2:
                unidade = getattr(produto, 'unidade_medida', '') if produto else ''
                label_quantidade = f"Quantidade ({unidade})" if unidade else "Quantidade"
                quantidade = st.number_input(
                    label_quantidade,
                    value=1.0,
                    min_value=0.001, 
                    step=1.0, 
                    format="%.3f"
                )
            
            with col3:
                if st.button("Adicionar", icon=":material/add:", disabled=produto is None):
                    try:
                        # Verificação final no momento do clique
                        if any(item["id_produto"] == produto.id for item in st.session_state.itens_temporarios):
                            st.error("Este produto já foi adicionado ao inventário!")
                            st.stop()
                        
                        inventario_service.adicionar_item(
                            inventario.id,
                            produto.id,
                            quantidade
                        )
                        st.session_state.itens_temporarios.append({
                            "id": None,  # Será atualizado após recarregar
                            "id_produto": produto.id,  # Novo campo para controle
                            "produto": produto.nome,
                            "quantidade": quantidade,
                            "unidade": unidade
                        })
                        st.rerun(scope="fragment")
                    except Exception as e:
                        st.error(str(e))

    if st.session_state.itens_temporarios and len(st.session_state.itens_temporarios) > 0:
        total_itens = len(st.session_state.itens_temporarios)

        with st.expander(f"**Total de itens: {total_itens}**", expanded=True, icon=":material/list:"):
            spec = [0.07, 0.5, 0.13, 0.11, 0.2]
            
            # Cabeçalho
            columns = st.columns(spec=spec, vertical_alignment="center")
            columns[0].button("**#**", type="tertiary", use_container_width=True)
            columns[1].button("**Produto**", type="tertiary", use_container_width=True)
            columns[2].button("**Qtde**", type="tertiary")
            columns[3].button("**UM**", type="tertiary")
            columns[4].button("**Remover**", type="tertiary")

            with st.container(border=True):
                # Carrega dados frescos do banco
                itens_db = inventario_service.listar_itens(inventario.id)
                
                # Atualiza a lista temporária com dados do banco
                st.session_state.itens_temporarios = [{
                    "id": item.id,
                    "id_produto": item.produto.id,
                    "produto": item.produto.nome,
                    "quantidade": item.quantidade_contada,
                    "unidade": item.produto.unidade_medida
                } for item in itens_db]
                
                for idx, item in enumerate(reversed(st.session_state.itens_temporarios), 1):
                    numero_item = total_itens - idx + 1
                    cols = st.columns(spec=spec, vertical_alignment="center")
                    
                    with cols[0]:
                        st.markdown(f"**{numero_item}.**")
                    
                    with cols[1]:
                        st.markdown(f"**{item['produto']}**")
                    
                    with cols[2]:
                        st.markdown(f"{format_decimal(item['quantidade'], 3)}")
                    
                    with cols[3]:
                        st.markdown(f"{item['unidade']}")
                    
                    with cols[4]:
                        # Função de callback para remoção
                        def remove_callback(item_id=item['id']):
                            # Remove o item do inventário
                            try:
                                inventario_service.remover_item(item_id)
                                # Força atualização imediata
                                st.session_state.itens_temporarios = [
                                    i for i in st.session_state.itens_temporarios
                                    if i['id'] != item_id
                                ]
                            except Exception as e:
                                st.error(f"Erro ao remover item: {str(e)}")

                        # Mapa de ícones para as operações
                        delete_option_map = {
                            "delete": ":material/delete:",
                            "confirm": ":material/check:",
                            "cancel": ":material/close:"
                        }

                        # Estado único para controle de confirmação
                        pill_state_key = f"pill_state_{item['id']}"
                        
                        # Inicializa o estado se necessário
                        if pill_state_key not in st.session_state:
                            st.session_state[pill_state_key] = "default"

                        # Lógica de renderização condicional
                        if st.session_state[pill_state_key] == "confirming":
                            # Modo de confirmação com check e close
                            selected_action = st.segmented_control(
                                "Confirmação",
                                options=["confirm", "cancel"],
                                format_func=lambda opt: delete_option_map[opt],
                                key=f"confirm_pills_{item['id']}",
                                label_visibility="collapsed",
                                disabled=inventario_encerrado
                            )

                            if selected_action == "confirm":
                                remove_callback(item['id'])
                                st.session_state[pill_state_key] = "deleted"
                                st.rerun(scope="fragment")
                            elif selected_action == "cancel":
                                st.session_state[pill_state_key] = "default"
                                st.rerun(scope="fragment")

                        else:
                            # Modo normal com ícone de lixeira
                            selected_action = st.pills(
                                "Ações",
                                options=["delete"],
                                format_func=lambda opt: delete_option_map[opt],
                                key=f"delete_pill_{item['id']}",
                                label_visibility="collapsed",
                                disabled=inventario_encerrado
                            )

                            if selected_action == "delete":
                                st.session_state[pill_state_key] = "confirming"
                                st.rerun(scope="fragment")