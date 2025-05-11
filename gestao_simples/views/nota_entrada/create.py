# views/nota_entrada/create.py
from services.nota_entrada_service import NotaEntradaService
from services.fornecedor_service import FornecedorService
from services.item_nota_entrada_service import ItemNotaEntradaService
from utils.validacoes import validar_nota_entrada, validar_item_nota_entrada, ValidationError
from models.item_nota_entrada import ItemNotaEntrada
from models.nota_entrada import NotaEntrada
import pandas as pd
from datetime import datetime
from streamlit_date_picker import date_picker, PickerType
import streamlit as st
from utils.format import format_brl
import copy

class NotaEntradaCreateView:
    def __init__(self):
        self.nota_entrada_service = NotaEntradaService()
        self.fornecedor_service = FornecedorService()
        self.item_service = ItemNotaEntradaService()
        self.render()

    def render(self):
        st.title("Nova Entrada")
        
        # Inicializa variáveis de sessão
        if "temp_items" not in st.session_state:
            st.session_state.temp_items = [ItemNotaEntrada()]
#        if "is_editing" not in st.session_state:
#            st.session_state.is_editing = False
#        if "itens_para_quantidade" not in st.session_state:
#            st.session_state.itens_para_quantidade = []
#        if "repeticoes" not in st.session_state:
#            st.session_state.repeticoes = {}

        if st.button("← Voltar", type="tertiary"):
            # Limpa todas as variáveis relacionadas à criação da NotaEntrada
            keys_to_reset = [
                "create_mode", "is_editing", "temp_items", "editing_items",
                "itens_para_quantidade", "repeticoes", "modal_repeticoes",
                "fornecedor_selecionado", "multiselect_itens_create"
            ]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]            
            st.rerun()
        
        with st.expander("**Dados da Nota**", expanded=True):
            col1, col2, col3 = st.columns([1, 2, 2])
            modelo = col1.text_input("Modelo")
            numero_nota_entrada = col2.text_input("Número da Nota")
            serie_nota_entrada = col3.text_input("Série da Nota")

            fornecedores = self.fornecedor_service.listar_fornecedores()
            fornecedor = st.selectbox(
                "Fornecedor",
                index=None,
                options=fornecedores,
                placeholder="Selecione um fornecedor",
                format_func=lambda f: f.nome,
                key='fornecedor_selecionado'
            )

            chave_acesso = st.text_input("Chave de acesso")
            url = st.text_input("URL")
            st.markdown("Data da emissão")
            data_emissao = date_picker(picker_type=PickerType.time, value=datetime.now(), key='date_picker')

        with st.expander("**Itens da Nota**", expanded=True):
            # Seção para adicionar itens históricos dentro do expander dos itens
            if fornecedor:
                if st.session_state.get("is_editing", False):
                    #st.warning("Finalize a edição antes de adicionar novos itens.")
                    itens_selecionados = []
                else:
                    with st.container():
                        itens_fornecedor = self.nota_entrada_service.listar_itens_unicos_por_fornecedor(fornecedor.id)
                        if itens_fornecedor:
                            col1, col2 = st.columns([0.8, 0.2], vertical_alignment="bottom")
                            itens_selecionados = col1.multiselect(
                                "Selecione itens para adicionar",
                                options=itens_fornecedor,
                                placeholder="Selecione quantos itens for preciso",
                                format_func=lambda item: (
                                    f"{item['codigo']} - {item['descricao']} | "
                                    f"Última compra: {item['data_emissao'].strftime('%d/%m/%Y')}"
                                ),
                                key='multiselect_itens_create'
                            )
                            if col2.button("Definir repetições", type='secondary'):
                                if itens_selecionados:
                                    st.session_state.modal_repeticoes = True
                                    st.session_state.itens_para_quantidade = itens_selecionados
                                else:
                                    st.warning("Selecione pelo menos um item primeiro")

                    if st.session_state.get('modal_repeticoes', False):
                        self._render_modal_repeticoes_create()

            # Renderiza o editor de itens
            self._render_items_editor()

        # Botão "Salvar NotaEntrada" desabilitado enquanto estiver em modo de edição
        if st.button("Salvar Nota", type="primary", disabled=st.session_state.get("is_editing", False)):
            self._save_nota_entrada(fornecedor, chave_acesso, data_emissao, url, numero_nota_entrada, serie_nota_entrada, modelo)

    def _render_items_editor(self):
        if not st.session_state.get("is_editing", False):
            items_df = pd.DataFrame([{
                'Cód. no Fornecedor': item.codigo_produto_fornecedor,
                'Descrição': item.descricao,
                'Quantidade': item.quantidade,
                'Unidade': item.unidade_medida,
                'Valor Unitário': item.valor,
            } for item in st.session_state.temp_items])
            items_df.dropna(how='all', inplace=True, ignore_index=True)
            self._sync_edits(items_df)
            st.table(items_df)

            col1, col2 = st.columns([.8, .3])
            if col1.button("Editar Itens"):
                st.session_state.editing_items = copy.deepcopy(st.session_state.temp_items)
                st.session_state.is_editing = True
                st.rerun()

            total_nota_entrada = (items_df['Quantidade'] * items_df['Valor Unitário']).sum()
            col2.metric("**Total da Nota:**", format_brl(total_nota_entrada))                  

        else:
            # Modo de edição: utiliza o estado temporário "editing_items"
            editing_items_df = pd.DataFrame([{
                'Cód. no Fornecedor': item.codigo_produto_fornecedor,
                'Descrição': item.descricao,
                'Quantidade': item.quantidade,
                'Unidade': item.unidade_medida,
                'Valor Unitário': item.valor,
            } for item in st.session_state.editing_items])
            editing_items_df.dropna(how='all', inplace=True, ignore_index=True)
            edited_df = st.data_editor(
                editing_items_df,
                num_rows="dynamic",
                column_config={
                    "Quantidade": st.column_config.NumberColumn(format="%.2f"),
                    "Valor Unitário": st.column_config.NumberColumn(format="%.2f"),
                    "Qtd. Grade": st.column_config.NumberColumn(format="%.1f")
                },
                use_container_width=True,
                key="editing_items_editor_create"
            )
            col1, col2 = st.columns(2)
            if col1.button("Confirmar Alterações"):
                success = self._sync_edits(edited_df)
                if success:
                    st.session_state.is_editing = False
                    del st.session_state.editing_items
                    st.rerun()
            if col2.button("Cancelar Edição"):
                st.session_state.is_editing = False
                del st.session_state.editing_items
                st.rerun()
            valid_df = edited_df.dropna(subset=['Quantidade', 'Valor Unitário'])
            total_nota_entrada = (valid_df['Quantidade'] * valid_df['Valor Unitário']).sum()
            st.metric("**Total da Nota:**", format_brl(total_nota_entrada))                

    def _sync_edits(self, edited_df):
        # Remove linhas totalmente vazias e valida cada item
        cleaned_df = edited_df.dropna(how='all').reset_index(drop=True)
        novos_itens = []
        errors = []
        # Como o ID não é exibido, presume-se que os itens existentes continuam sendo atualizados
        for i, row in cleaned_df.iterrows():
            item = ItemNotaEntrada(
                codigo_produto_fornecedor=row.get('Cód. no Fornecedor'),
                descricao=row.get('Descrição'),
                quantidade=row.get('Quantidade'),
                unidade_medida=row.get('Unidade'),
                valor=row.get('Valor Unitário'),
            )
            try:
                validar_item_nota_entrada(item)
                novos_itens.append(item)
            except ValidationError as ve:
                errors.append(f"Linha {i+1}: {', '.join(ve.errors)}")
        if errors:
            for error in errors:
                st.error(error)
            return False
        if not novos_itens:
            return False
        st.session_state.temp_items = novos_itens
        return True

    def _save_nota_entrada(self, fornecedor, chave_acesso, data_emissao, url, numero_nota_entrada, serie_nota_entrada, modelo):
        try:
            novo_nota_entrada = NotaEntrada(
                fornecedor_id=fornecedor.id if fornecedor else None,
                chave_acesso=chave_acesso if chave_acesso else None,
                modelo=modelo,
                data_emissao=data_emissao,
                url=url,
                numero_nota_entrada=numero_nota_entrada,
                serie_nota_entrada=serie_nota_entrada,
                total_nota_entrada=0.0
            )
            
            validar_nota_entrada(novo_nota_entrada)
            
            if not st.session_state.temp_items:
                raise ValidationError("Adicione pelo menos um item à Nota")
            
            for item in st.session_state.temp_items:
                validar_item_nota_entrada(item)
            
            total_nota_entrada = sum(item.quantidade * item.valor for item in st.session_state.temp_items)
            novo_nota_entrada.total_nota_entrada = total_nota_entrada
            
            itens_data = [item.__dict__ for item in st.session_state.temp_items]
            for item in itens_data:
                item.pop('_sa_instance_state', None)
                item.pop('id', None)
            
            self.nota_entrada_service.criar_nota_entrada_atomica(novo_nota_entrada, itens_data)
            
            st.success("Nota cadastrada com sucesso!")
            
            st.session_state.temp_items = []
            st.session_state.create_mode = False
            st.rerun()
            
        except ValidationError as e:
            if e.errors:
                for error in e.errors:
                    st.error(error)
            else:
                st.error(f"Erro ao validar Nota. {str(e)}")
        except Exception as e:
            st.error(f"Erro ao cadastrar Nota: {str(e)}")               

    @st.dialog("Quantas vezes o item deve repetir?")
    def _render_modal_repeticoes_create(self):
        with st.container():
            if "itens_para_quantidade" not in st.session_state:
                st.session_state.itens_para_quantidade = []
            if "repeticoes" not in st.session_state:
                st.session_state.repeticoes = {}
            with st.form("repeticoes_form_create"):
                for idx, item in enumerate(st.session_state.itens_para_quantidade):
                    st.write(f"**{item['codigo']} - {item['descricao']}** ({item['unidade']})")
                    st.session_state.repeticoes[idx] = st.number_input(
                        "Quantidade de repetições:",
                        min_value=1,
                        value=st.session_state.repeticoes.get(idx, 1),
                        key=f"qtd_create_{idx}"
                    )
                    st.divider()
                col1, col2 = st.columns([1, 3])
                if col1.form_submit_button("Confirmar", type="primary"):
                    self._processar_repeticoes_create()
                if col2.form_submit_button("Cancelar"):
                    st.session_state.modal_repeticoes = False
                    st.rerun()

    def _processar_repeticoes_create(self):
        novos_itens = []
        for idx, item in enumerate(st.session_state.itens_para_quantidade):
            qtd = st.session_state.repeticoes.get(idx, 1)
            for _ in range(qtd):
                novo_item = ItemNotaEntrada(
                    codigo_produto_fornecedor=item['codigo'],
                    descricao=item['descricao'],
                    quantidade=1.0,  # Valor inicial
                    unidade_medida=item['unidade'],
                    valor=item['valor'],
                )
                novos_itens.append(novo_item)

        st.session_state.temp_items.extend(novos_itens)

        # Limpa estados temporários
        if "itens_para_quantidade" in st.session_state:
            del st.session_state.itens_para_quantidade
        if "modal_repeticoes" in st.session_state:
            del st.session_state.modal_repeticoes
        st.session_state.multiselect_itens_create = []
        st.session_state.repeticoes = {}
        st.rerun()