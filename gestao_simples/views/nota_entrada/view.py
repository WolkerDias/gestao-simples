# views/nota_entrada/view.py
import streamlit as st
import pandas as pd
from services.nota_entrada_service import NotaEntradaService
from services.item_nota_entrada_service import ItemNotaEntradaService
from services.fornecedor_service import FornecedorService
from models.nota_entrada import NotaEntrada
from models.item_nota_entrada import ItemNotaEntrada
from utils.format import format_chave_acesso, format_cnpj, format_datetime, format_brl

class NotaEntradaDetailView:
    def __init__(self, nota_entrada_id: int):
        self.nota_entrada_id = nota_entrada_id
        self.nota_entrada_service = NotaEntradaService()
        self.item_service = ItemNotaEntradaService()
        self.fornecedor_service = FornecedorService()
        self.nota_entrada = self._carregar_nota_entrada()
        self.render()

    def _carregar_nota_entrada(self) -> NotaEntrada:
        nota_entrada = self.nota_entrada_service.buscar_nota_entrada_por_id(self.nota_entrada_id)
        if not nota_entrada:
            st.error("Nota não encontrada")
            st.session_state.view_mode = False
            st.rerun()
        return nota_entrada

    def render(self):
        st.title("Detalhes da Nota")
        
        # Botão de voltar
        if st.button("← Voltar para Lista"):
            st.session_state.view_mode = False
            st.rerun()

        # Seção de dados principais
        with st.container(border=True):
            st.subheader("Dados Gerais")

            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            with col1:
                st.write("Modelo:", f"{self.nota_entrada.modelo}" if self.nota_entrada.modelo else "Não informado")
            with col2:
                st.write("Número:", f"{self.nota_entrada.numero_nota_entrada}" if self.nota_entrada.numero_nota_entrada else "Não informado")
            with col3:
                st.write("Série:", f"{self.nota_entrada.serie_nota_entrada}" if self.nota_entrada.serie_nota_entrada else "Não informado")
            with col4:
                st.write(f"Data Emissão:", format_datetime(self.nota_entrada.data_emissao))         
            
            # Obter dados do fornecedor
            fornecedor = self.fornecedor_service.buscar_fornecedor_por_id(self.nota_entrada.fornecedor_id) if self.nota_entrada.fornecedor_id else None
            
            col1, col2 = st.columns([.3, .7])
            with col1:
                st.write("CNPJ:", format_cnpj(fornecedor.cnpj) if fornecedor else "Não informado")
                
            with col2:
                st.write("Fornecedor:", fornecedor.nome if fornecedor else "Não informado")
            
            st.write("Chave de Acesso:", format_chave_acesso(self.nota_entrada.chave_acesso) if self.nota_entrada.chave_acesso else "Não informado")
                
            st.write("URL:", self.nota_entrada.url or "Não informado")

        # Seção de itens
        with st.container(border=True):
            st.subheader("Itens da Nota")
            
            # Carregar itens
            itens = self.item_service.listar_itens_por_nota_entrada(self.nota_entrada_id)
            
            # Criar DataFrame para exibição
            df = pd.DataFrame([{
                "Código": item.codigo_produto_fornecedor,
                "Descrição": item.descricao,
                "Quantidade": f"{item.quantidade:.2f} {item.unidade_medida}",
                "Valor Unitário": format_brl(item.valor),
                "Valor Total": format_brl(item.valor * item.quantidade),
            } for item in itens])

            # Exibir tabela
            st.table(df)
            _, col2 = st.columns([.8, .3])
            col2.metric("**Total:**", format_brl(self.nota_entrada.total_nota_entrada))

        # Seção de ações
        with st.container():
            st.write("")  # Espaçamento
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🖨️ Exportar PDF", type="secondary"):
                    self._exportar_pdf()

    def _exportar_pdf(self):
        # Lógica fictícia para exportação
        st.toast("Exportando para PDF...")
        # Implementação real dependeria de biblioteca de PDF