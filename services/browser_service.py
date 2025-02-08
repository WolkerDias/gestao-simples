# services/browser_service.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st
from utils.logger import logger
import time
import requests
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Suprime avisos SSL

class BrowserService:
    def __init__(self):
        self.driver = None
        self.chrome_driver_path = None
        
    def get_chrome_driver_path(self):
        try:
            # Define o caminho absoluto para o diretório .wdm
            os.environ["WDM_LOCAL"] = "2"
            wdm_dir = os.path.join(os.path.expanduser("~"), ".wdm")  # Exemplo: C:\Users\seu_usuario\.wdm
            os.environ["WDM_LOCAL_PATH"] = wdm_dir
            os.makedirs(wdm_dir, exist_ok=True)  # Cria o diretório se não existir

            # Baixa ou usa o ChromeDriver do cache
            driver_path = ChromeDriverManager().install()
            st.write(f"ChromeDriver encontrado em: {driver_path}")
            return driver_path
        except Exception as e:
            st.error(f"Erro ao obter ChromeDriver: {str(e)}")
            raise
        
    def initialize_driver(self):
        """Initialize Chrome driver with custom options."""
        try:
            st.write("Iniciando configuração do Chrome...")
            
            # Configurar opções do Chrome
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--start-maximized')
            
            # Adicionar configurações para melhorar performance
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            
            # Obter caminho do ChromeDriver
            if not self.chrome_driver_path:
                self.chrome_driver_path = self.get_chrome_driver_path()
            
            st.write("Iniciando Chrome...")
            service = Service(executable_path=self.chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            st.write("Chrome iniciado com sucesso!")
            return True
            
        except Exception as e:
            st.error(f"Erro ao inicializar Chrome: {str(e)}")
            logger.error(f"Error initializing browser: {str(e)}")
            return False

    def wait_for_captcha_solution(self, url, timeout=300):
        """
        Opens URL and waits for user to solve CAPTCHA.
        Returns the page source after CAPTCHA is solved.
        """
        try:
            with st.status("Processando QR Code", expanded=False) as status:
                if not self.driver:
                    status.update(label="Inicializando navegador...")
                    if not self.initialize_driver():
                        raise Exception("Falha ao inicializar o navegador")

                status.update(label="Acessando URL...")
                self.driver.get(url)
                
                status.update(label="Aguardando resolução do CAPTCHA", state="running")
                
                start_time = time.time()
                while (time.time() - start_time) < timeout:
                    try:
                        # Verificar se o driver ainda está ativo
                        current_url = self.driver.current_url
                        
                        # Verificar se página foi carregada
                        content_present = len(self.driver.find_elements(By.ID, 'tabResult')) > 0
                        
                        if content_present:
                            status.update(label="CAPTCHA resolvido!", state="complete")
                            return self.driver.page_source
                        
                        time.sleep(2)
                    
                    except Exception as e:
                        status.update(label=f"Erro: {str(e)}", state="error")
                        break

                status.update(label="Tempo limite excedido", state="error")
                raise TimeoutException("Processo de CAPTCHA interrompido")

        except Exception as e:
            st.error(f"Erro durante processo de CAPTCHA: {str(e)}")
            logger.error(f"Erro durante espera do CAPTCHA: {str(e)}")
            raise
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except Exception:
                    pass

    def get_page_with_captcha_handling(self, url):
        """
        Main method to handle page access with CAPTCHA detection.
        Returns page source after successful access.
        """
        try:
            st.toast("Iniciando acesso à página...")
            
            # Primeira tentativa com requests
            try:
                st.toast("Tentando acesso direto...")
                response = requests.get(url, timeout=10)
                st.toast(f"Status code: {response.status_code}")
                
                # Se a resposta for bem-sucedida e não contiver CAPTCHA
                if response.status_code == 200 and not any(term in response.text.lower() 
                    for term in ["captcha", "certificate", "certificado", "validação"]):
                    st.success("Acesso direto bem-sucedido!")
                    return response.text
                else:
                    st.warning("Detectada necessidade de CAPTCHA no acesso direto.")
                    
            except requests.RequestException as e:
                st.warning(f"Falha no acesso direto: {str(e)}")
            
            st.info("""
                **📢 Atenção:**  
                Um navegador será aberto automaticamente. Por favor:
                1. Resolva o CAPTCHA na nova janela
                2. Clique no botão 'Consultar'
                3. Aguarde o processamento automático
                """)
            html_content = self.wait_for_captcha_solution(url)
            
            if html_content:
                st.success("Conteúdo obtido com sucesso!")
                return html_content
            else:
                raise Exception("Falha ao obter conteúdo da página")
            
        except Exception as e:
            st.error(f"Erro no processamento da página: {str(e)}")
            logger.error(f"Erro no processamento da página: {str(e)}")
            raise