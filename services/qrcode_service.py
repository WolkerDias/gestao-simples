# services/qrcode_service.py
from PIL import Image, ImageEnhance
import numpy as np
import cv2
from pyzbar.pyzbar import decode
from urllib.parse import urlparse, parse_qs, quote
import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
from models.nfce import NFCe
from models.fornecedor import Fornecedor
from utils.logger import logger
from config.settings import CAPTURE_DIR

class QRCodeService:

    def preprocess_image(self, image):
        """Pré-processa a imagem para melhor detecção de QR Code."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        return gray

    def detect_qrcode(self, image, max_size=800):
        """Detecta QR Codes usando pyzbar."""
        try:
            if isinstance(image, Image.Image):
                image.thumbnail((max_size, max_size))
                image = np.array(image.convert("RGB"))

            h, w = image.shape[:2]
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            preprocessed_image = self.preprocess_image(image)
            decoded_objects = decode(preprocessed_image)

            if decoded_objects:
                return decoded_objects[0].data.decode("utf-8")
            return None
        except Exception as e:
            logger.error(f"Erro na detecção do QR Code: {str(e)}")
            raise

    def process_qr_code_url(self, url):
        """Processa o URL do QR Code para extrair os dados."""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            param = query_params.get('p', [None])[0]

            if param:
                encoded_param = quote(param, encoding='utf-8')
                encoded_url = f"https://www.dfe.ms.gov.br/nfce/qrcode/?p={encoded_param}"

                response = requests.get(encoded_url)
                if response.status_code == 200:
                    return self.extract_nfce_data(response.text), encoded_url
                else:
                    logger.error(f"Erro ao acessar a página. Status Code: {response.status_code}")
                    raise Exception(f"Erro ao acessar a página. Status Code: {response.status_code}")

        except Exception as e:
            logger.error(f"Erro ao processar URL do QR Code: {str(e)}")
            raise

    def extract_nfce_data(self, html):
        """Extrai dados de produtos do HTML da NFC-e."""
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # Extrai dados da NFCe
            chave_acesso = soup.find('span', class_='chave').text.replace(' ', '')
            cnpj = soup.find('div', class_='text').text.split('CNPJ:')[1].strip().replace('.', '').replace('/', '').replace('-', '')
            razao_social = soup.find('div', class_='txtTopo').text
            data_emissao_str = soup.select_one("strong:-soup-contains('Emissão:')").next_sibling.text.split('-')[0].strip()
            data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y %H:%M:%S')

            # Cria objetos do modelo
            fornecedor = Fornecedor(
                nome=razao_social,
                cnpj=cnpj
            )

            nfce = NFCe(
                chave_acesso=chave_acesso,
                fornecedor_id=None,  # Será definido após salvar o fornecedor
                data_emissao=data_emissao
            )

            # Extrai itens
            itens = []
            for item in soup.find('table', id='tabResult').find_all('tr'):
                codigo_produto_fornecedor = item.find('span', class_='RCod').text.split(":")[1].replace(')', '').strip()
                descricao = item.find('span', class_='txtTit').text
                unidade = item.find('span', class_='RUN').text.split(":")[1].strip().upper()
                quantidade = float(item.find('span', class_='Rqtd').text.split(":")[1].replace(',', '.'))
                valor = float(item.find('span', class_='RvlUnit').text.split(":")[1].replace('R$', '').strip().replace(',', '.'))

                item_dict = {
                    'codigo_produto_fornecedor': codigo_produto_fornecedor,
                    'produto': None,
                    'descricao': descricao,
                    'quantidade': quantidade,
                    'unidade_medida': unidade,
                    'quantidade_por_grade': None,
                    'valor': valor
                }
                itens.append(item_dict)

            return {
                'fornecedor': fornecedor,
                'nfce': nfce,
                'itens': itens
            }

        except Exception as e:
            logger.error(f"Erro ao extrair dados da NFCe: {str(e)}")
            raise

    def save_image(self, image, prefix="captured"):
        """Salva a imagem processada no diretório de capturas."""
        try:
            save_path = f"{CAPTURE_DIR}/{prefix}_image_{int(time.time())}.jpg"
            image.save(save_path)
            logger.info(f"Imagem salva em {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Erro ao salvar imagem: {str(e)}")
            raise

    def process_uploaded_image(self, image):
        """Processa imagem enviada via upload."""
        try:
            enhancer = ImageEnhance.Contrast(image)
            image_enhanced = enhancer.enhance(2.0)
            image_bw = self.convert_to_bw(image_enhanced)
            image_cv = np.array(image_bw, dtype=np.uint8)
            image_cv = cv2.cvtColor(image_cv, cv2.COLOR_GRAY2BGR)
            return image_cv, image_bw
        except Exception as e:
            logger.error(f"Erro ao processar imagem enviada: {str(e)}")
            raise

    def process_camera_image(self, image):
        """Processa imagem capturada pela câmera."""
        try:
            image_cv = np.array(image, dtype=np.uint8)
            image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
            return image_cv, Image.fromarray(image_cv)
        except Exception as e:
            logger.error(f"Erro ao processar imagem da câmera: {str(e)}")
            raise

    def convert_to_bw(self, image, threshold=128):
        """Converte a imagem para preto e branco usando um threshold."""
        image_gray = image.convert("L")
        return image_gray.point(lambda x: 255 if x > threshold else 0, mode="L")

    def correct_image_orientation(self, image):
        """Corrige a orientação da imagem usando metadados EXIF."""
        try:
            if hasattr(image, '_getexif') and image._getexif() is not None:
                from PIL import ExifTags
                exif = dict(image._getexif().items())
                orientation = next((k for k, v in ExifTags.TAGS.items() if v == 'Orientation'), None)
                
                if orientation and orientation in exif:
                    orientation_value = exif[orientation]
                    if orientation_value == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation_value == 6:
                        image = image.rotate(-90, expand=True)
                    elif orientation_value == 8:
                        image = image.rotate(90, expand=True)
            return image
        except Exception as e:
            logger.error(f"Erro ao corrigir orientação da imagem: {str(e)}")
            return image