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
import uuid

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
                "fornecedor_selecionado", "multiselect_itens_create",
                "row_counts", "custom_items"
            ]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]            
            st.rerun()
            
        
        with st.expander("**Dados da Nota**", expanded=True):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
            modelo = col1.text_input("Modelo", value=65)
            numero_nota_entrada = col2.text_input("Número da Nota")
            serie_nota_entrada = col3.text_input("Série da Nota", value=1)
            # Input de data/hora com segundos
            # Define o valor padrão apenas uma vez
            if "data_emissao_default" not in st.session_state:
                hora_default = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                st.session_state["data_emissao_default"] = hora_default.strftime("%d/%m/%Y %H:%M:%S")

            datetime_str = col4.text_input(
                "Data de Emissão",
                value=st.session_state["data_emissao_default"],
                help="Data e hora de emissão da nota fiscal. Use o formato DD/MM/AAAA HH:MM:SS",
                key="data_emissao_input"
            )
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

            # Validação e conversão da data
            try:
                if datetime_str:
                    data_emissao = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                st.error(f"❌ Formato de data inválido. Use DD/MM/AAAA HH:MM:SS. \nEx. {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

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
                modelo=modelo if modelo else None,
                data_emissao=data_emissao,
                url=url,
                numero_nota_entrada=numero_nota_entrada,
                serie_nota_entrada=serie_nota_entrada if serie_nota_entrada else None,
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

    def _add_row(self, idx):
        st.session_state.row_ids[idx].append(str(uuid.uuid4()))

    def _remove_row(self, idx, r_id, key_qtd, key_val):
        if len(st.session_state.row_ids[idx]) > 1:
            st.session_state.row_ids[idx].remove(r_id)
            # Limpa o lixo da memória
            if key_qtd in st.session_state: del st.session_state[key_qtd]
            if key_val in st.session_state: del st.session_state[key_val]

    def _add_custom(self):
        st.session_state.custom_items.append({'id': str(uuid.uuid4()), 'unidade': 'UN'})

    def _remove_custom(self, c_id, keys_to_delete):
        # Filtra a lista removendo apenas o item com o ID especificado
        st.session_state.custom_items = [c for c in st.session_state.custom_items if c.get('id') != c_id]
        for k in keys_to_delete:
            if k in st.session_state: del st.session_state[k]               

    @st.dialog("Detalhes dos Itens", width="large")
    def _render_modal_repeticoes_create(self):
        if "itens_para_quantidade" not in st.session_state:
            st.session_state.itens_para_quantidade = []
            
        if "row_ids" not in st.session_state:
            st.session_state.row_ids = {
                idx: [str(uuid.uuid4())] for idx in range(len(st.session_state.itens_para_quantidade))
            }
            
        if "custom_items" not in st.session_state:
            st.session_state.custom_items = []

        subtotal_geral = 0.0

        st.markdown("### Itens do Fornecedor")
        for idx, item in enumerate(st.session_state.itens_para_quantidade):
            st.markdown(f"**{item['codigo']} - {item['descricao']}** ({item['unidade']})")
            
            row_ids = st.session_state.row_ids.get(idx, [])

            for r_id in row_ids:
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1], vertical_alignment="bottom")
                
                key_qtd = f"qtd_{idx}_{r_id}"
                key_val = f"val_{idx}_{r_id}"

                qtd = c1.number_input("Qtd:", min_value=0.01, value=st.session_state.get(key_qtd, 1.0), format="%.2f", key=key_qtd)
                val = c2.number_input("Valor Unit.:", min_value=0.0, value=st.session_state.get(key_val, float(item.get('valor', 0.0))), format="%.2f", key=key_val)
                
                subtotal_linha = qtd * val
                subtotal_geral += subtotal_linha
                
                c3.metric("Subtotal", format_brl(subtotal_linha))

                with c4:
                    bc1, bc2 = st.columns(2)
                    # Usando on_click para alterar a lista ANTES da tela atualizar
                    bc1.button("➕", key=f"add_{idx}_{r_id}", help="Adicionar variação", 
                               on_click=self._add_row, args=(idx,))
                               
                    bc2.button("🗑️", key=f"rem_{idx}_{r_id}", help="Remover variação", 
                               on_click=self._remove_row, args=(idx, r_id, key_qtd, key_val), 
                               disabled=(len(st.session_state.row_ids[idx]) <= 1))
            st.divider()

        st.markdown("### Itens Adicionais (Manuais)")
        for custom in st.session_state.custom_items:
            c_id = custom['id']
            c1, c2, c3, c4, c5 = st.columns([2, 3, 1.5, 1.5, 1], vertical_alignment="bottom")
            
            key_cod = f"cust_cod_{c_id}"
            key_desc = f"cust_desc_{c_id}"
            key_cqtd = f"cust_qtd_{c_id}"
            key_cval = f"cust_val_{c_id}"
            keys_to_delete = [key_cod, key_desc, key_cqtd, key_cval]
            
            cod = c1.text_input("Código", value=st.session_state.get(key_cod, ""), key=key_cod)
            desc = c2.text_input("Descrição", value=st.session_state.get(key_desc, ""), key=key_desc)
            qtd = c3.number_input("Qtd", min_value=0.01, value=st.session_state.get(key_cqtd, 1.0), format="%.2f", key=key_cqtd)
            val = c4.number_input("Valor Unit.", min_value=0.0, value=st.session_state.get(key_cval, 0.0), format="%.2f", key=key_cval)
            
            subtotal_linha = qtd * val
            subtotal_geral += subtotal_linha

            c5.button("🗑️", key=f"rem_cust_{c_id}", help="Remover item manual", 
                      on_click=self._remove_custom, args=(c_id, keys_to_delete))

        st.button("➕ Adicionar Item Novo", on_click=self._add_custom)
        st.divider()

        st.markdown("### Resumo Financeiro")
        c1, c2, c3 = st.columns(3)
        c1.metric("**Subtotal Geral**", format_brl(subtotal_geral))
        
        desc_acres = c2.number_input("Desconto (-) / Acréscimo (+)", value=st.session_state.get('desc_acres_input', 0.0), key="desc_acres_input", format="%.2f")
        
        total_final = subtotal_geral + desc_acres
        c3.metric("**Total Final**", format_brl(total_final))

        st.write("")
        c_btn1, c_btn2 = st.columns([1, 4])
        if c_btn1.button("Confirmar Lançamentos", type="primary"):
            self._processar_repeticoes_create()
        if c_btn2.button("Cancelar"):
            self._limpar_modal_repeticoes()
            st.rerun()

    def _processar_repeticoes_create(self):
        novos_itens = []
        subtotal_geral = 0.0
        itens_temp_processados = []

        # 1. Coleta itens do fornecedor processando via ID único
        for idx, item in enumerate(st.session_state.itens_para_quantidade):
            row_ids = st.session_state.row_ids.get(idx, [])
            for r_id in row_ids:
                qtd = st.session_state.get(f"qtd_{idx}_{r_id}", 1.0)
                val = st.session_state.get(f"val_{idx}_{r_id}", float(item.get('valor', 0.0)))
                subtotal_geral += qtd * val
                
                itens_temp_processados.append({
                    'codigo': item['codigo'],
                    'descricao': item['descricao'],
                    'quantidade': qtd,
                    'unidade': item['unidade'],
                    'valor_original': val
                })

        # 2. Coleta itens manuais puxando direto do estado (muito mais seguro)
        for custom in st.session_state.custom_items:
            c_id = custom['id']
            cod = st.session_state.get(f"cust_cod_{c_id}", "SEM_COD")
            desc = st.session_state.get(f"cust_desc_{c_id}", "Item Manual")
            qtd = st.session_state.get(f"cust_qtd_{c_id}", 1.0)
            val = st.session_state.get(f"cust_val_{c_id}", 0.0)
            
            subtotal_geral += qtd * val
            
            itens_temp_processados.append({
                'codigo': cod,
                'descricao': desc,
                'quantidade': qtd,
                'unidade': custom.get('unidade', 'UN'),
                'valor_original': val
            })

        # 3. Aplicar o Rateio
        desc_acres = st.session_state.get('desc_acres_input', 0.0)
        total_final = subtotal_geral + desc_acres
        fator = (total_final / subtotal_geral) if subtotal_geral > 0 else 1.0

        # 4. Criar Objetos
        for it in itens_temp_processados:
            valor_rateado = it['valor_original'] * fator
            novo_item = ItemNotaEntrada(
                codigo_produto_fornecedor=it['codigo'],
                descricao=it['descricao'],
                quantidade=it['quantidade'],
                unidade_medida=it['unidade'],
                valor=valor_rateado
            )
            novos_itens.append(novo_item)

        st.session_state.temp_items.extend(novos_itens)
        self._limpar_modal_repeticoes()
        st.rerun()

    def _limpar_modal_repeticoes(self):
        """Limpa as variáveis temporárias usadas no modal para evitar lixo de memória"""
        keys_to_clean = [
            "itens_para_quantidade", "modal_repeticoes", 
            "row_ids", "custom_items", "desc_acres_input" 
        ]
        for k in keys_to_clean:
            if k in st.session_state:
                del st.session_state[k]
        
        st.session_state.multiselect_itens_create = []