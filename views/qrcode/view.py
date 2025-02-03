# views/qrcode/view.py
import streamlit as st
from PIL import Image
import pandas as pd
from services.qrcode_service import QRCodeService
from services.fornecedor_service import FornecedorService
from services.nfce_service import NFCeService
from services.item_nfce_service import ItemNFCeService
from utils.message_handler import message_handler, MessageType



class QRCodeView:
    def __init__(self):
        self.qrcode_service = QRCodeService()
        self.fornecedor_service = FornecedorService()
        self.nfce_service = NFCeService()
        self.item_service = ItemNFCeService()
        self.render()

    def render(self):
        st.title("📱 Leitor de QR Code")

        message_handler.display_toast_message()
        
        # Seleção do modo de captura
        option_map = {
            0: ":material/upload: Upload de Imagem",
            1: ":material/camera: Câmera ao Vivo",
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
        else:
            self._handle_camera_mode()

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

    def _process_image(self, image, source_type):
        try:
            # Corrige orientação e salva
            image = self.qrcode_service.correct_image_orientation(image)
            save_path = self.qrcode_service.save_image(image, source_type)
            st.success(f"Imagem salva em {save_path}")

            # Processa imagem baseado na fonte
            if source_type == "uploaded":
                image_cv, image_processed = self.qrcode_service.process_uploaded_image(image)
            else:
                image_cv, image_processed = self.qrcode_service.process_camera_image(image)

            if image_cv is not None:
                st.image(image_processed, caption="Imagem Processada", use_container_width=True)
                self._process_qr_code(image_cv)

        except Exception as e:
            st.error(f"Erro ao processar imagem: {str(e)}")

    def _process_qr_code(self, image_cv):
        try:
            qr_data = self.qrcode_service.detect_qrcode(image_cv)
            if qr_data:
                nfce_data, qrcode_url = self.qrcode_service.process_qr_code_url(qr_data)
                if nfce_data:
                    self._display_nfce_data(nfce_data, qrcode_url)
            else:
                st.error("Nenhum QR Code detectado na imagem.")
        except Exception as e:
            st.error(f"Erro ao processar QR Code: {str(e)}")

    @st.dialog("Nova NFCe via QR Code", width="large")
    def _display_nfce_data(self, nfce_data, qrcode_url):
        st.success("QR Code detectado e processado com sucesso!")
        
        # Exibe dados da NFCe
        st.subheader("Dados da NFCe")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Fornecedor:** {nfce_data['fornecedor'].nome}")
            st.write(f"**CNPJ:** {nfce_data['fornecedor'].cnpj}")
        with col2:
            st.write(f"**Chave de Acesso:** {nfce_data['nfce'].chave_acesso}")
            st.write(f"**Data Emissão:** {nfce_data['nfce'].data_emissao}")

        # Editor de itens
        st.subheader("Itens da NFCe")
        edited_df = st.data_editor(
            pd.DataFrame(nfce_data['itens']),
            column_config={
                "produto": st.column_config.SelectboxColumn(
                    "produto",
                    help="Classifique o produto",
                    width="medium",
                    options=[
                        "Verdura",
                        "Açúcar",
                        "Arroz",
                        "Outros",
                    ],
                )
            },
            hide_index=True,
        )

        if st.button("Salvar no Banco de Dados"):
            self._save_to_database(nfce_data, edited_df, qrcode_url)

    def _save_to_database(self, nfce_data, edited_df, qrcode_url):
        try:
            # Verificar se o fornecedor já existe no banco de dados
            fornecedor = self.fornecedor_service.buscar_fornecedor_por_cnpj(nfce_data['fornecedor'].cnpj)
            if not fornecedor:
                # Salva fornecedor
                fornecedor = self.fornecedor_service.criar_fornecedor(nfce_data['fornecedor'])
                
            # Atualiza NFCe com o ID do fornecedor e URL do QR Code
            nfce_data['nfce'].fornecedor_id = fornecedor.id
            nfce_data['nfce'].qrcode_url = qrcode_url
            nfce = self.nfce_service.criar_nfce(nfce_data['nfce'])
            
            # Salva os itens
            for item in edited_df.to_dict('records'):
                item['nfce_id'] = nfce.id
                self.item_service.criar_item(item)
            
            # Clear the file uploader and camera input
            st.session_state["qr_method"] = 0  # Reset to upload mode
            if "file_uploader_key" not in st.session_state:
                st.session_state["file_uploader_key"] = 0
            if "camera_input_key" not in st.session_state:
                st.session_state["camera_input_key"] = 0
            
            st.session_state["file_uploader_key"] += 1
            st.session_state["camera_input_key"] += 1
            
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