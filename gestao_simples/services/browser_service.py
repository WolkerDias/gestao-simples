# services/browser_service.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from config.settings import CHROME_DRIVER_CACHE_PATH
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

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
        self.cache_file = CHROME_DRIVER_CACHE_PATH # Arquivo para armazenar o caminho
        
    def _load_cached_driver_path(self):
        """Carrega o caminho do driver do arquivo de cache, se existir e for válido."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                cached_path = f.read().strip()
                if os.path.exists(cached_path):
                    return cached_path
        return None
    
    def _save_cached_driver_path(self, path):
        """Salva o caminho do driver no arquivo de cache."""
        with open(self.cache_file, "w") as f:
            f.write(path)

    def get_chrome_driver_path(self):
        """Obtém o caminho do ChromeDriver, usando cache quando possível."""
        cached_path = self._load_cached_driver_path()
        if cached_path:
            st.write("✅ Usando ChromeDriver cacheado.")
            return cached_path
        
        try:
            st.write("🔍 Procurando ChromeDriver...")
            # Configuração do diretório de cache
            os.environ["WDM_LOCAL"] = "2"
            wdm_dir = os.path.join(os.path.expanduser("~"), ".wdm")
            os.environ["WDM_LOCAL_PATH"] = wdm_dir
            os.makedirs(wdm_dir, exist_ok=True)

            # Busca o driver e salva no cache
            driver_path = ChromeDriverManager().install()
            self._save_cached_driver_path(driver_path)
            st.success(f"ChromeDriver encontrado em: {driver_path}")
            return driver_path
        except Exception as e:
            st.error(f"Erro ao obter ChromeDriver: {str(e)}")
            raise
    
    def initialize_driver(self):
        """Inicializa o driver, com tratamento para falhas no cache."""
        try:
            st.write("🚀 Iniciando configuração do Chrome...")
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')

            if not self.chrome_driver_path:
                self.chrome_driver_path = self.get_chrome_driver_path()

            service = Service(executable_path=self.chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            st.success("Chrome iniciado com sucesso!")
            return True
        except WebDriverException as e:
            st.warning("Falha ao usar ChromeDriver cacheado. Atualizando...")
            # Limpa o cache e tenta novamente
            self.chrome_driver_path = None
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            return self.initialize_driver()  # Recursão controlada
        except Exception as e:
            st.error(f"Erro crítico ao inicializar Chrome: {str(e)}")
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
                        if len(self.driver.find_elements(By.ID, 'tabResult')) > 0:
                            modelo = 65 #nfce
                        elif len(self.driver.find_elements(By.ID, 'aba_nft_0')) > 0:
                            modelo = 55 #nfe
                        else:
                            modelo = None

                        if modelo:
                            status.update(label="CAPTCHA resolvido!", state="complete")
                            return self.driver.page_source, modelo
                        
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
                    return response.text, 65 #nfce
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
            html_content, modelo = self.wait_for_captcha_solution(url)
            
            if html_content:
                st.success("Conteúdo obtido com sucesso!")
                return html_content, modelo
            else:
                raise Exception("Falha ao obter conteúdo da página")
            
        except Exception as e:
            st.error(f"Erro no processamento da página: {str(e)}")
            logger.error(f"Erro no processamento da página: {str(e)}")
            raise