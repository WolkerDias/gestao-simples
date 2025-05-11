# views/estoque/auditoria/list.py
import streamlit as st
import pandas as pd
from services.auditoria_service import AuditoriaService
from services.inventario_estoque_service import InventarioEstoqueService
from utils.format import format_datetime, format_brl, format_value_brl

class AuditoriaListView:
    def __init__(self):
        self.auditoria_service = AuditoriaService()
        self.inventario_service = InventarioEstoqueService()
        self.render()

    def render(self):
        st.title("📊 Auditoria de Estoques - Método PEPS")
        
        # Carrega dados para filtros
        inventarios = self._carregar_inventarios()
        produtos = self._carregar_produtos()

        # Filtros
        referencia_selecionada, produto_selecionado = self._construir_filtros(inventarios, produtos)

        # Botão de pesquisa
        if referencia_selecionada and produto_selecionado:
            dados = self.auditoria_service.obter_dados_auditoria(
                referencia_inventario=referencia_selecionada if referencia_selecionada != "Último Inventário" else None
            )
            
            if dados:
                df = self._format_dataframe(dados, produto_selecionado)

                on = st.toggle("Mostrar tudo", value=False, help="Ative para mostrar todos os itens, incluindo os zerados.")

                if not on:
                    # Filtra saldos diferentes de zero, se a opção não estiver ativada
                    df = df[df['Saldo (UN)'] != 0]

                df['ID'] = df['ID'].astype(str)
                df['Data Entrada (Lote)'] = df['Data Entrada (Lote)'].apply(format_datetime)
                df['Custo Unitário'] = df['Custo Unitário'].apply(format_brl)

                values_un=['Quantidade (UN)', 'Consumo (UN)', 'Saldo (UN)']
                values_brl=['Custo Total', 'Custo Consumido', 'Saldo Financeiro']

                df = df.pivot_table(
                    index=['ID', 'Produto', 'Data Entrada (Lote)', 'Custo Unitário'],
                    values=values_un + values_brl,
                    aggfunc='sum', margins=True, margins_name='Total'
                ).reset_index()

                for value in values_un:
                    df[value] = df[value].apply(format_value_brl, decimals=3)

                for value in values_brl:
                    df[value] = df[value].apply(format_brl)

                self._exibir_tabela(df)
                st.markdown("---")
                self._export_to_csv(df)
            else:
                st.warning("Nenhum dado encontrado para os filtros selecionados.")

    def _carregar_inventarios(self):
        inventarios = [inv.referencia for inv in self.inventario_service.listar_inventarios()]
        inventarios.insert(0, "Último Inventário")
        return inventarios

    def _carregar_produtos(self):
        dados = self.auditoria_service.obter_dados_auditoria()
        produtos = list({d['nome'] for d in dados})
        produtos.sort()
        produtos.insert(0, "Todos")
        return produtos

    def _construir_filtros(self, inventarios, produtos):
        col1, col2 = st.columns([1, 2])
        with col1:
            referencia = st.selectbox(
                "Referência do Inventário:",
                options=inventarios,
                index=0,
                help="Selecione o período de inventário para auditoria"
            )
        with col2:
            produto = st.selectbox(
                "Filtrar por Produto:",
                options=produtos,
                index=0,
                help="Filtre os resultados por produto específico"
            )
        return referencia, produto

    def _format_dataframe(self, dados, filtro_produto):
        df = pd.DataFrame([{
            "ID": item['produto_id'],
            "Produto": item['nome'],
            "Data Entrada (Lote)": item['data_emissao'],
            "Quantidade (UN)": item['quantidade_unidades'],
            "Custo Unitário": item['valor_unitario'],
            "Custo Total": item['valor_total_lote'],
            "Consumo (UN)": item['quantidade_consumida'],
            "Saldo (UN)": item['saldo_remanescente'],
            "Custo Consumido": item['valor_consumido'],
            "Saldo Financeiro": item['valor_saldo_remanescente']
        } for item in dados if filtro_produto == "Todos" or item['nome'] == filtro_produto])

        return df  

    def _exibir_tabela(self, df):
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )


    def _export_to_csv(self, df):

        csv_data = df.to_csv(index=False, sep=';').encode('utf-8-sig')
        
        st.download_button(
            label="⬇️ Exportar para CSV",
            data=csv_data,
            file_name='auditoria_estoque.csv',
            mime='text/csv',
            help="Download dos dados filtrados em formato CSV"
        )
