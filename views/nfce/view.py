# views/nfce/view.py
import streamlit as st
import pandas as pd
from services.item_nfce_service import ItemNFCeService
from services.fornecedor_service import FornecedorService
from services.nfce_service import NFCeService
from streamlit_date_picker import date_picker, PickerType

@st.dialog("Visualizar NFCe", width="large")
def show_view_nfce(nfce):
    item_service = ItemNFCeService()
    fornecedor_service = FornecedorService()
    nfce_service = NFCeService()
    
    # Buscar informações do fornecedor
    fornecedor = fornecedor_service.buscar_fornecedor_por_id(nfce.fornecedor_id)
    
    # Tabs para diferentes funcionalidades
    tab_view, tab_edit, tab_itens = st.tabs(["Visualizar", "Editar", "Itens"])
    
    # Tab de Visualização
    with tab_view:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Fornecedor:** {fornecedor.nome}")
            st.write("**QR Code:**")
            st.code(nfce.qrcode_url if nfce.qrcode_url else "QR Code não cadastrado", language=None)
        
        with col2:
            st.write(f"**Data de Emissão:** {pd.to_datetime(nfce.data_emissao).strftime('%d/%m/%Y %H:%M:%S')}")
            st.write("**Chave de Acesso:**")
            st.code(nfce.chave_acesso, language=None)

        # Botão de excluir na aba de visualização
        with st.expander("🗑️ Excluir NFCe"):
            if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                try:
                    nfce_service.deletar_nfce(nfce.id)
                    st.success(f"NFCe excluída com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir NFCe: {e}")

        # Lista de itens em modo visualização
        st.subheader("Itens da NFCe")
        try:
            itens = item_service.listar_itens_por_nfce(nfce_id=nfce.id)
            
            if itens:
                df_itens = pd.DataFrame([{
                    'Cód. Prod. Fornecedor': item.codigo_produto_fornecedor,
                    'Produto': item.produto,
                    'Descrição': item.descricao,
                    'Quantidade': f"{item.quantidade} {item.unidade_medida}",
                    'Qtd. por Grade': item.quantidade_por_grade or '-',
                    'Valor Unit.': f"R$ {item.valor:.2f}",
                    'Valor Total': f"R$ {(item.quantidade * item.valor):.2f}"
                } for item in itens])
                
                st.dataframe(
                    df_itens,
                    use_container_width=True,
                    hide_index=True
                )
                
                total_nfce = sum(item.quantidade * item.valor for item in itens)
                st.markdown(f"**Total da NFCe:** R$ {total_nfce:.2f}")
            else:
                st.info("Nenhum item cadastrado para esta NFCe")

        except Exception as e:
            st.error(f"Erro ao carregar itens: {str(e)}")

    # Tab de Edição
    with tab_edit:
        fornecedores = fornecedor_service.listar_fornecedores()

        with st.form("editar_nfce"):
            fornecedor = st.selectbox(
                "Selecione o Fornecedor", 
                options=fornecedores, 
                format_func=lambda f: f.nome,
                index=next((i for i, f in enumerate(fornecedores) if f.id == nfce.fornecedor_id), 0)
            )
            chave_acesso = st.text_input("Chave de Acesso", value=nfce.chave_acesso)
            st.markdown("##### Data da emissão")
            data_emissao = date_picker(picker_type=PickerType.time, value=nfce.data_emissao, key='date_picker')
            qrcode_url = st.text_input("QR Code", value=nfce.qrcode_url)

            submitted = st.form_submit_button("Atualizar")
            
            if submitted:
                nfce.chave_acesso = chave_acesso
                nfce.data_emissao = data_emissao
                nfce.qrcode_url = qrcode_url
                nfce.fornecedor_id = fornecedor.id
                
                nfce_service.atualizar_nfce(nfce)
                st.success("NFCe atualizado com sucesso!")
                st.rerun()

    # Tab de Itens
    with tab_itens:
        try:
            # Listar itens existentes
            itens = item_service.listar_itens_por_nfce(nfce_id=nfce.id)
            
            if itens:
                df_itens = pd.DataFrame([{
                    'ID': item.id,
                    'Cód. Prod. Fornecedor': item.codigo_produto_fornecedor,
                    'Produto': item.produto,
                    'Descrição': item.descricao,
                    'Quantidade': f"{item.quantidade} {item.unidade_medida}",
                    'Qtd. por Grade': item.quantidade_por_grade or '-',
                    'Valor Unit.': f"R$ {item.valor:.2f}",
                    'Valor Total': f"R$ {(item.quantidade * item.valor):.2f}"
                } for item in itens])
                
                item_table = st.dataframe(
                    df_itens,
                    use_container_width=True,
                    hide_index=True,
                    selection_mode="multi-row",
                    on_select="rerun",
                )
                
                total_nfce = sum(item.quantidade * item.valor for item in itens)
                st.markdown(f"**Total da NFCe:** R$ {total_nfce:.2f}")

                selected_itens = item_table.selection.rows
                with st.expander("🗑️ Excluir Itens Selecionados"):
                    if selected_itens and st.button("Confirmar Exclusão de Itens Selecionados", type="primary", use_container_width=True):
                        try:
                            for index in selected_itens:
                                item_id = df_itens.iloc[index]['ID']
                                item_service.deletar_item(item_id)
                            st.success("Itens excluídos com sucesso!")
                            st.rerun(scope="fragment")
                        except Exception as e:
                            st.error(f"Erro ao excluir itens: {str(e)}")
            else:
                st.info("Nenhum item cadastrado para esta NFCe")

        except Exception as e:
            st.error(f"Erro ao carregar itens: {str(e)}")

        # Formulário para adicionar novo item
        with st.expander("➕ Adicionar Itens"):
            with st.form("novo_item", clear_on_submit=True):
                st.subheader("Adicionar Novo Item")
                
                col1, col2 = st.columns(2)
                with col1:
                    codigo_produto_fornecedor = st.number_input("Cód. Prod. Fornecedor", min_value=0, step=1)
                    produto = st.text_input("Nome do Produto")
                    descricao = st.text_area("Descrição do Produto", height=100)
                    unidade_medida = st.selectbox(
                        "Unidade de Medida",
                        options=['UN', 'KG', 'L', 'M', 'M2', 'M3', 'PC', 'CX', 'DZ', 'CT']
                    )
                
                with col2:
                    quantidade = st.number_input("Quantidade", min_value=0.01, step=0.01)
                    qtd_grade = st.number_input("Quantidade por Grade", min_value=0.0, step=0.01)
                    valor = st.number_input("Valor Unitário (R$)", min_value=0.01, step=0.01)
                    st.markdown(f"**Valor Total: R$ {(quantidade * valor):.2f}**")

                submitted = st.form_submit_button("Adicionar Item")
                
                if submitted:
                    try:
                        novo_item = {
                            'nfce_id': nfce.id,
                            'codigo_produto_fornecedor': codigo_produto_fornecedor or None,
                            'produto': produto or None,
                            'descricao': descricao,
                            'quantidade': quantidade,
                            'unidade_medida': unidade_medida,
                            'quantidade_por_grade': qtd_grade or None,
                            'valor': valor
                        }
                        item_service.criar_item(novo_item)
                        st.success("Item adicionado com sucesso!")
                        st.rerun(scope="fragment")
                        
                    except Exception as e:
                        st.error(f"Erro ao adicionar item: {str(e)}")