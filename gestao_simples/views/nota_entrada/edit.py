# views/nota_entrada/edit.py
from services.nota_entrada_service import NotaEntradaService
from services.fornecedor_service import FornecedorService
from services.item_nota_entrada_service import ItemNotaEntradaService
from utils.validacoes import validar_nota_entrada, ValidationError, validar_item_nota_entrada
from models.item_nota_entrada import ItemNotaEntrada
import pandas as pd
from datetime import datetime
from streamlit_date_picker import date_picker, PickerType
import streamlit as st
from utils.format import format_brl
import copy

class NotaEntradaEditView:
    def __init__(self, nota_entrada_id):
        self.nota_entrada_id = nota_entrada_id
        self.nota_entrada_service = NotaEntradaService()
        self.fornecedor_service = FornecedorService()
        self.item_service = ItemNotaEntradaService()
        self.nota_entrada = self.nota_entrada_service.buscar_nota_entrada_por_id(nota_entrada_id)
        self.render()

    def render(self):
        if not self.nota_entrada:
            st.error("Nota não encontrada")
            st.session_state.edit_mode = False
            st.rerun()
            return

        st.title("Editar Nota")
        
        if st.button("← Voltar", type="tertiary"):
            # Limpa todas as variáveis do session_state relacionadas à edição da Nota
            keys_to_reset = [
                "edit_mode", "is_editing", "temp_items", "editing_items",
                "itens_para_quantidade", "repeticoes", "modal_repeticoes",
                "fornecedor_selecionado", "multiselect_itens_edit"
            ]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        with st.expander("**Dados da Nota**", expanded=True):
            col1, col2, col3 = st.columns([1, 2, 2])
            modelo = col1.text_input("Modelo", value=self.nota_entrada.modelo)
            numero_nota_entrada = col2.text_input("Número da Nota", value=self.nota_entrada.numero_nota_entrada)
            serie_nota_entrada = col3.text_input("Série da Nota", value=self.nota_entrada.serie_nota_entrada)
            
            fornecedores = self.fornecedor_service.listar_fornecedores()
            fornecedor_selecionado = next(
                (f for f in fornecedores if f.id == self.nota_entrada.fornecedor_id),
                None
            )
            fornecedor = st.selectbox(
                "Fornecedor", 
                options=fornecedores,
                index=0 if not self.nota_entrada.fornecedor_id else fornecedores.index(fornecedor_selecionado),
                format_func=lambda f: f.nome
            )

            chave_acesso = st.text_input("Chave de acesso", value=self.nota_entrada.chave_acesso)
            url = st.text_input("URL", value=self.nota_entrada.url)
            st.markdown("Data da emissão")
            data_emissao = date_picker(
                picker_type=PickerType.time, 
                value=self.nota_entrada.data_emissao if self.nota_entrada.data_emissao else datetime.now(),
                key='date_picker_edit'
            )
        
        with st.expander("**Itens da Nota**", expanded=True):
            # Carrega os itens existentes, se ainda não estiverem no estado
            if "temp_items" not in st.session_state:
                st.session_state.temp_items = self.item_service.listar_itens_por_nota_entrada(self.nota_entrada_id)
            
            # Se o fornecedor estiver definido, permite adicionar itens históricos via multiselect
            if fornecedor:
                if st.session_state.get("is_editing", False):
                    #st.warning("Finalize a edição dos itens antes de adicionar novos.")
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
                                key='multiselect_itens_edit'
                            )
                            if col2.button("Definir repetições", type='secondary'):
                                if itens_selecionados:
                                    st.session_state.modal_repeticoes = True
                                    st.session_state.itens_para_quantidade = itens_selecionados
                                else:
                                    st.warning("Selecione pelo menos um item primeiro")

                    if st.session_state.get('modal_repeticoes', False):
                        self._render_modal_repeticoes_edit()
            
            # Exibe o editor dos itens
            self._render_items_editor()

        # O botão para salvar alterações fica desabilitado enquanto estiver em modo de edição
        if st.button("Salvar Alterações", type="primary", disabled=st.session_state.get("is_editing", False)):
            self._update_nota_entrada(fornecedor, chave_acesso, data_emissao, url, numero_nota_entrada, serie_nota_entrada, modelo)

    def _render_items_editor(self):
        # Se não estiver em modo de edição, exibe os itens atuais e um botão para iniciar a edição
        if not st.session_state.get("is_editing", False):
            items_df = pd.DataFrame([{
                'Cód. no Fornecedor': item.codigo_produto_fornecedor,
                'Descrição': item.descricao,
                'Quantidade': item.quantidade,
                'Unidade': item.unidade_medida,
                'Valor Unitário': item.valor,
            } for item in st.session_state.temp_items])
            items_df.dropna(how='all', inplace=True, ignore_index=True)
            st.table(items_df)
            if st.button("Editar Itens"):
                st.session_state.editing_items = copy.deepcopy(st.session_state.temp_items)
                st.session_state.is_editing = True
                st.rerun()
        else:
            # Modo de edição: utiliza o estado temporário "editing_items"
            editing_items_df = pd.DataFrame([{
                'Cód. no Fornecedor': item.codigo_produto_fornecedor,
                'Descrição': item.descricao,
                'Quantidade': item.quantidade,
                'Unidade': item.unidade_medida,
                'Valor Unitário': item.valor,
                # O ID não é exibido, mas pode ser mantido internamente se necessário
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
                key="editing_items_editor_edit"
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
            st.error("Adicione pelo menos um item à Nota.")
            return False
        st.session_state.temp_items = novos_itens
        return True

    def _update_nota_entrada(self, fornecedor, chave_acesso, data_emissao, url, numero_nota_entrada, serie_nota_entrada, modelo):
        try:
            total_nota_entrada = sum(item.quantidade * item.valor for item in st.session_state.temp_items)
            
            # Identifica os IDs originais para itens removidos
            original_ids = {item.id for item in self.item_service.listar_itens_por_nota_entrada(self.nota_entrada_id)}
            current_ids = {item.id for item in st.session_state.temp_items if item.id}
            ids_para_excluir = original_ids - current_ids
            
            # Prepara os itens para atualização (converte para dicionário)
            itens_data = [{
                'id': item.id,
                'codigo_produto_fornecedor': item.codigo_produto_fornecedor,
                'descricao': item.descricao,
                'quantidade': item.quantidade,
                'unidade_medida': item.unidade_medida,
                'valor': item.valor,
                'nota_entrada_id': self.nota_entrada_id
            } for item in st.session_state.temp_items]

            # Atualiza os dados principais da Nota
            self.nota_entrada.fornecedor_id = fornecedor.id if fornecedor else None
            self.nota_entrada.modelo = modelo
            self.nota_entrada.chave_acesso = chave_acesso
            self.nota_entrada.data_emissao = data_emissao
            self.nota_entrada.url = url
            self.nota_entrada.numero_nota_entrada = numero_nota_entrada
            self.nota_entrada.serie_nota_entrada = serie_nota_entrada
            self.nota_entrada.total_nota_entrada = total_nota_entrada
            
            validar_nota_entrada(self.nota_entrada)

            self.nota_entrada_service.atualizar_nota_entrada_atomica(
                self.nota_entrada,
                itens_data,
                ids_para_excluir
            )
            
            st.success("Nota atualizada com sucesso!")
            st.session_state.temp_items = []
            st.session_state.edit_mode = False
            st.rerun()
            
        except ValidationError as e:
            for error in e.errors:
                st.error(error)
        except Exception as e:
            st.error(f"Erro ao atualizar Nota: {str(e)}")

    @st.dialog("Quantas vezes o item deve repetir?")
    def _render_modal_repeticoes_edit(self):
        with st.container():
            if "itens_para_quantidade" not in st.session_state:
                st.session_state.itens_para_quantidade = []
            if "repeticoes" not in st.session_state:
                st.session_state.repeticoes = {}
            with st.form("repeticoes_form_edit"):
                for idx, item in enumerate(st.session_state.itens_para_quantidade):
                    st.write(f"**{item['codigo']} - {item['descricao']}** ({item['unidade']})")
                    st.session_state.repeticoes[idx] = st.number_input(
                        "Quantidade de repetições:",
                        min_value=1,
                        value=st.session_state.repeticoes.get(idx, 1),
                        key=f"qtd_edit_{idx}"
                    )
                    st.divider()
                col1, col2 = st.columns([1, 3])
                if col1.form_submit_button("Confirmar", type="primary"):
                    self._processar_repeticoes_edit()
                if col2.form_submit_button("Cancelar"):
                    st.session_state.modal_repeticoes = False
                    st.rerun()

    def _processar_repeticoes_edit(self):
        novos_itens = []
        for idx, item in enumerate(st.session_state.itens_para_quantidade):
            qtd = st.session_state.repeticoes.get(idx, 1)
            for _ in range(qtd):
                novo_item = ItemNotaEntrada(
                    codigo_produto_fornecedor=item['codigo'],
                    descricao=item['descricao'],
                    quantidade=1.0,
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
        st.session_state.multiselect_itens_edit = []
        st.session_state.repeticoes = {}
        st.rerun()
