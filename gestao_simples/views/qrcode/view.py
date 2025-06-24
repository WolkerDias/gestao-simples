# views/qrcode/view.py
import streamlit as st
from PIL import Image
import pandas as pd
from services.qrcode_service import QRCodeService
from services.fornecedor_service import FornecedorService
from services.nota_entrada_service import NotaEntradaService
from services.item_nota_entrada_service import ItemNotaEntradaService
from utils.message_handler import message_handler, MessageType
from utils.format import format_brl, format_cnpj, format_datetime, format_chave_acesso

class QRCodeView:
    def __init__(self):
        self.qrcode_service = QRCodeService()
        self.fornecedor_service = FornecedorService()
        self.nota_entrada_service = NotaEntradaService()
        self.item_service = ItemNotaEntradaService()
        self.render()

    def render(self):
        st.title("📱 Leitor de QR Code")

        message_handler.display_toast_message()
        
        # Seleção do modo de captura
        option_map = {
            0: ":material/upload: Upload de Imagem",
            1: ":material/camera: Câmera ao Vivo",
            2: ":material/link: Chave de Acesso ou URL"
        }

        # Seleção do método de entrada de QR Code com valor inicial 0
        selection = st.segmented_control(
            "Método de Entrada de QR Code",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",
            #key="qr_method", 
            default=0
        )

        if selection == 0:
            self._handle_upload_mode()
        elif selection == 1:
            self._handle_camera_mode()
        else:
            self._handle_url_mode()

    def _handle_upload_mode(self):
        key = st.session_state.get("file_uploader_key", 0)
        uploaded_file = st.file_uploader(
            "Faça upload de uma imagem contendo o QR Code:", 
            type=["jpg", "jpeg", "png"],
            key=f"uploader_{key}"
        )
        
        if uploaded_file is not None:
            self._process_image(Image.open(uploaded_file), "uploaded")

    def _handle_camera_mode(self):
        self._add_camera_styles()
        key = st.session_state.get("camera_input_key", 0)
        camera_input = st.camera_input(
            "Capture uma imagem contendo o QR Code:",
            key=f"camera_{key}"
        )
        
        if camera_input is not None:
            self._process_image(Image.open(camera_input), "captured")

    def _handle_url_mode(self):
        """Manipula a entrada de URL para processamento direto do QR Code"""
        key = st.session_state.get("url_input_key", 0)

        help_text = """
        📌 Estrutura do Código de Acesso
        
            O código de acesso da NFC-e possui 44 dígitos:
            
            🔹 1 a 2 → Código da UF (Ex: 35 para SP, 50 para MS)
            🔹 3 a 6 → Ano e mês de emissão (AAMM)
            🔹 7 a 20 → CNPJ do emitente
            🔹 21 a 22 → Modelo do documento MS (55 para NF-e e 65 para NFC-e)
            🔹 23 a 24 → Série da NFC-e
            🔹 25 a 29 → Número da NFC-e
            🔹 30 a 32 → Código numérico aleatório (gerado pelo emissor)
            🔹 33 a 43 → Código único para evitar duplicidade
            🔹 44 → Dígito verificador (cálculo módulo 11)
        """
                
        url = st.text_input(
            "Digite a chave de acesso ou a URL do QR Code da NotaEntrada:",
            placeholder="Chave de Acesso ou URL do QR Code",
            key=f"url_input_{key}",
            help=help_text
        )
        
        if url:
            self._process_url(url)

    def _process_url(self, url):
        """Processa uma URL diretamente sem necessidade de imagem"""
        try:
            # Processa a URL como se fosse um QR Code decodificado
            nota_entrada_data, url = self.qrcode_service.process_url_or_chave(url)
            
            if nota_entrada_data:
                self._display_nota_entrada_data(nota_entrada_data, url)
            else:
                st.error("Não foi possível extrair dados da NotaEntrada desta URL.")

        except Exception as e:
            st.error(f"Falha ao processar URL: {str(e)}")
            st.exception(e)

    def _process_image(self, image, source_type):
        try:
            # Corrige orientação e salva
            image = self.qrcode_service.correct_image_orientation(image)
            expander = st.expander("Ver imagem")
            expander.image(image, caption="Imagem QR Code", use_container_width=True)

            # Processa imagem baseado na fonte
            if source_type == "uploaded":
                image_cv, image_processed = self.qrcode_service.process_uploaded_image(image)
            else:
                image_cv, image_processed = self.qrcode_service.process_camera_image(image)

            if image_cv is not None:
                self._process_qr_code(image_cv)

        except Exception as e:
            st.error(f"Erro ao processar imagem: {str(e)}")

    def _process_qr_code(self, image_cv):
        try:
            qr_data = self.qrcode_service.detect_qrcode(image_cv)
            if qr_data:
                nota_entrada_data, url = self.qrcode_service.process_url_or_chave(qr_data)
                if nota_entrada_data:
                    self._display_nota_entrada_data(nota_entrada_data, url)
            else:
                st.error("Nenhum QR Code detectado na imagem.")
        except Exception as e:
            st.error(f"Erro ao processar QR Code: {str(e)}")

    @st.dialog("Nova NotaEntrada via QR Code", width="large")
    def _display_nota_entrada_data(self, nota_entrada_data, url):
        st.success("QR Code detectado e processado com sucesso!")
        
        # Exibe dados da NotaEntrada
        st.subheader("Dados da NotaEntrada:")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            col1.write(f"**Fornecedor:** {nota_entrada_data['fornecedor'].nome}")
            col2.write(f"**CNPJ:** {format_cnpj(nota_entrada_data['fornecedor'].cnpj)}")

        with st.container(border=True):
            st.write(f"**Chave de Acesso:** {format_chave_acesso(nota_entrada_data['nota_entrada'].chave_acesso)}")
            col1, col2, col3 = st.columns([1, 1, 2])
            col1.write(f"**Número:** {nota_entrada_data['nota_entrada'].numero_nota_entrada}")
            col2.write(f"**Série:** {nota_entrada_data['nota_entrada'].serie_nota_entrada}")
            col3.write(f"**Data Emissão:** {format_datetime(nota_entrada_data['nota_entrada'].data_emissao)}")

        # Editor de itens
        st.subheader("Itens da NotaEntrada:")
        edited_df = st.data_editor(
            pd.DataFrame(nota_entrada_data['itens']),
            hide_index=True,
        )

        total_calc_nota_entrada = (edited_df.quantidade * edited_df.valor).sum()
        total_nota_entrada = nota_entrada_data['nota_entrada'].total_nota_entrada
        diferenca = round(total_calc_nota_entrada - total_nota_entrada, 2)

        # Layout com três colunas
        col1, col2, col3 = st.columns(3)

        # Total NotaEntrada na SEFAZ
        col1.metric("**Total NotaEntrada (SEFAZ)**", format_brl(total_nota_entrada))

        # Total Calculado com destaque para diferença (desconto ou acréscimo)
        col2.metric("**Total Calculado**", format_brl(total_calc_nota_entrada), delta=f"{format_brl(diferenca)}", delta_color='off')

        # Diferença com percentual
        percentual_diferenca = (diferenca / total_calc_nota_entrada) * 100
        col3.metric("**Diferença Detectada**", format_brl(diferenca), delta=f"{percentual_diferenca:.2f}%", delta_color='normal')

        # Mensagens dinâmicas conforme o valor da diferença
        if diferenca > 0:
            st.markdown(
                f"""
                ### ⚠️ **Atenção: Desconto Detectado**  
                A nota fiscal na SEFAZ apresenta um **desconto de {format_brl(abs(diferenca))}** 
                (**{abs(percentual_diferenca):.2f}%**).  
                
                **Por favor, verifique se o desconto está correto no sistema.**
                """
            )
        elif diferenca < 0:
            st.markdown(
                f"""
                ### 📈 **Acréscimo Detectado**  
                A nota fiscal na SEFAZ apresenta um **acréscimo de {format_brl(diferenca)}** 
                (**{percentual_diferenca:.2f}%**).  
                
                **Por favor, confirme se o acréscimo está correto no sistema.**
                """
            )
        else:
            st.markdown("✅ Tudo certo! Não há diferenças entre o cálculo e a SEFAZ.")

        if st.button("Salvar no Banco de Dados"):
            self._save_to_database(nota_entrada_data, edited_df, url)

    def _save_to_database(self, nota_entrada_data, edited_df, url):
        try:
            # Verificar se o fornecedor já existe no banco de dados
            fornecedor = self.fornecedor_service.buscar_fornecedor_por_cnpj(nota_entrada_data['fornecedor'].cnpj)
            if not fornecedor:
                # Salva fornecedor
                fornecedor = self.fornecedor_service.criar_fornecedor(nota_entrada_data['fornecedor'])
                # Se chegou aqui, deu sucesso
                message_handler.add_message(
                    MessageType.SUCCESS,
                    f"Fornecedor {nota_entrada_data['fornecedor'].nome} cadastrado com sucesso!"
                )
                
            # Atualiza NotaEntrada com o ID do fornecedor e URL do QR Code
            nota_entrada_data['nota_entrada'].fornecedor_id = fornecedor.id
            nota_entrada_data['nota_entrada'].url = url
            self.nota_entrada_service.criar_nota_entrada_atomica(
                nota_entrada_data['nota_entrada'],
                edited_df.to_dict('records')
            )
            
            # Clear the file uploader and camera input
            st.session_state["qr_method"] = 0  # Reset to upload mode
            if "file_uploader_key" not in st.session_state:
                st.session_state["file_uploader_key"] = 0
            if "camera_input_key" not in st.session_state:
                st.session_state["camera_input_key"] = 0
            if "url_input_key" not in st.session_state:
                st.session_state["url_input_key"] = 0
            
            st.session_state["file_uploader_key"] += 1
            st.session_state["camera_input_key"] += 1
            st.session_state["url_input_key"] += 1
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Erro ao salvar dados: {str(e)}")

    def _add_camera_styles(self):
        st.markdown(
            """
            <style>
            [data-testid="stCameraInput"] video {
                border: 4px solid green; /* Borda verde sólida */
                width: 200px;  /* Largura quadrada */
                height: 200px; /* Altura quadrada */
                object-fit: cover; /* Ajusta o conteúdo para preencher a área quadrada */
                border-radius: 10px; /* Bordas arredondadas para um efeito mais profissional */
                margin: auto; /* Centraliza o elemento */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )