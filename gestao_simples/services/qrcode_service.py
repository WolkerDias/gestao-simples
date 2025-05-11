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
from models.nota_entrada import NotaEntrada
from models.fornecedor import Fornecedor
from utils.logger import logger
from config.settings import CAPTURE_DIR
from services.browser_service import BrowserService
import streamlit as st
import re
# Remove warnings 
from bs4 import XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
class QRCodeService:
    def __init__(self):
        self.browser_service = BrowserService()

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

    def process_url_or_chave(self, url):
        """Processa URLs ou chaves de acesso NFC-e para extrair dados"""
        try:
            st.toast("Iniciando processamento da entrada...")
            
            # Verifica se a entrada é uma chave de acesso (44 dígitos)
            cleaned_input = re.sub(r'\D', '', url)  # Remove não dígitos
            if len(cleaned_input) == 44:
                st.toast("Detectada chave de acesso NFC-e. Construindo URL...")
                modelo = int(cleaned_input[20:22])
                if modelo == 65:
                    # URL específica para NFC-e do MS
                    encoded_url = f"https://www.dfe.ms.gov.br/nfce/consulta/?tpAmb=0&chNFe={cleaned_input}&redirect=true"
                elif modelo == 55:
                    # URL específica para NF-e do MS
                    encoded_url = f"https://www.dfe.ms.gov.br/nfe/consulta/?tpAmb=1&chNFe={cleaned_input}&redirect=true"
                
                param = cleaned_input
            else:
                # Processamento padrão para URLs com parâmetro 'p'
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                param = query_params.get('p', [None])[0]
                
                if not param:
                    raise Exception("Nenhum parâmetro 'p' encontrado ou chave inválida")
                
                encoded_param = quote(param, encoding='utf-8')
                encoded_url = f"https://www.dfe.ms.gov.br/nfce/qrcode/?p={encoded_param}"

            st.toast("Obtendo dados da NotaEntrada...")
            html_content, modelo = self.browser_service.get_page_with_captcha_handling(encoded_url)
            
            if html_content:
                st.toast("Extraindo dados do HTML...")
                if modelo == 65: #nfce
                    return self.extract_nfce_data(html_content, modelo), encoded_url
                elif modelo == 55: #nfe
                    return self.extract_nfe_data(html_content, modelo), encoded_url
            else:
                raise Exception("Falha ao obter conteúdo da página")

        except Exception as e:
            st.error(f"Erro ao processar entrada: {str(e)}")
            logger.error(f"Erro no processamento: {str(e)}")
            raise

    def extract_nfce_data(self, html, modelo):
        """Extrai dados de produtos do HTML da NFC-e."""
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # Extrai dados da NotaEntrada
            modelo=modelo
            chave_acesso = soup.find('span', class_='chave').text.replace(' ', '')
            cnpj = soup.find('div', class_='text').text.split('CNPJ:')[1].strip().replace('.', '').replace('/', '').replace('-', '')
            razao_social = soup.find('div', class_='txtTopo').text
            numero_nota_entrada = soup.select_one("strong:-soup-contains('Número:')").next_sibling.text.strip()
            serie_nota_entrada = soup.select_one("strong:-soup-contains('Série:')").next_sibling.text.strip()
            data_emissao_str = soup.select_one("strong:-soup-contains('Emissão:')").next_sibling.text.split('-')[0].strip()
            data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y %H:%M:%S')
            total_nota_entrada = float(soup.find('span', class_='txtMax').text.replace(',', '.'))

            # Cria objetos do modelo
            fornecedor = Fornecedor(
                nome=razao_social,
                cnpj=cnpj
            )

            nota_entrada = NotaEntrada(
                modelo=modelo,
                chave_acesso=chave_acesso,
                fornecedor_id=None,  # Será definido após salvar o fornecedor
                data_emissao=data_emissao,
                numero_nota_entrada=numero_nota_entrada,
                serie_nota_entrada=serie_nota_entrada,
                total_nota_entrada=total_nota_entrada
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
                    'descricao': descricao,
                    'quantidade': quantidade,
                    'unidade_medida': unidade,
                    'valor': valor
                }
                itens.append(item_dict)

            return {
                'fornecedor': fornecedor,
                'nota_entrada': nota_entrada,
                'itens': itens
            }

        except Exception as e:
            logger.error(f"Erro ao extrair dados da NotaEntrada: {str(e)}")
            raise

    def extract_nfe_data(self, html, modelo):
        """Extrai dados de produtos do HTML da NFe utilizando IDs das abas."""
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            modelo=modelo
            # Chave de Acesso (Dados Gerais)
            chave_acesso = soup.select_one("label:-soup-contains('Chave de Acesso')").next_sibling.text.replace(' ', '')

            # IDs das abas relevantes
            dados_gerais_aba = soup.find('div', id='aba_nft_0')
            emitente_aba = soup.find('div', id='aba_nft_1')
            produtos_aba = soup.find('div', id='aba_nft_3')

            # Emitente (aba 1)
            cnpj = emitente_aba.find('label', string='CNPJ').find_next('span').text.replace('.', '').replace('/', '').replace('-', '')
            razao_social = emitente_aba.find('label', string='Nome / Razão Social').find_next('span').text.strip()

            # Dados Básicos (aba 0)
            numero_nota = dados_gerais_aba.find('label', string='Número').find_next('span').text.strip()
            serie_nota = dados_gerais_aba.find('label', string='Série').find_next('span').text.strip()
            data_emissao_str = dados_gerais_aba.find('label', string='Data de Emissão').find_next('span').text.split('-')[0].strip()
            data_emissao = datetime.strptime(data_emissao_str, '%d/%m/%Y %H:%M:%S')

            # Valor Total da NFe
            total_nota = float((dados_gerais_aba.select_one('#NFe > fieldset:nth-child(1) > table > tbody > tr > td:nth-child(6) > span').text).replace('.', '').replace(',', '.'))

            # Itens (aba 3)
            itens = []
            if produtos_aba:
                for produto in produtos_aba.find_all('table', class_='toggle box'):
                    descricao = produto.find('td', class_='fixo-prod-serv-descricao').span.text.strip() if produto.find('td', class_='fixo-prod-serv-descricao') else ''
                    quantidade = float(produto.find('td', class_='fixo-prod-serv-qtd').span.text.replace(',', '.')) if produto.find('td', class_='fixo-prod-serv-qtd') else 0.0
                    unidade = produto.find('td', class_='fixo-prod-serv-uc').span.text.strip() if produto.find('td', class_='fixo-prod-serv-uc') else ''
                    valor = float(produto.find('td', class_='fixo-prod-serv-vb').span.text.replace('.', '').replace(',', '.')) / quantidade
                    
                    # Código do produto
                    codigo = ''
                    detalhes = produto.find_next('table', class_='toggable box')
                    if detalhes:
                        codigo_label = detalhes.find('label', string='Código do Produto')
                        if codigo_label:
                            codigo_span = codigo_label.find_next('span')
                            codigo = codigo_span.text.strip() if codigo_span else ''

                    itens.append({
                        'codigo_produto_fornecedor': codigo,
                        'descricao': descricao,
                        'quantidade': quantidade,
                        'unidade_medida': unidade,
                        'valor': valor,
                    })

            return {
                'fornecedor': Fornecedor(nome=razao_social, cnpj=cnpj),
                'nota_entrada': NotaEntrada(
                    modelo=modelo,
                    chave_acesso=chave_acesso,
                    numero_nota_entrada=numero_nota,
                    serie_nota_entrada=serie_nota,
                    data_emissao=data_emissao,
                    total_nota_entrada=total_nota,
                    fornecedor_id=None
                ),
                'itens': itens
            }

        except Exception as e:
            logger.error(f"Erro ao extrair dados da NFe: {str(e)}")
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