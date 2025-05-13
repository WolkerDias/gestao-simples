# setup.py
from cx_Freeze import setup, Executable

executables = [
    Executable('app_launcher.py', base='Win32GUI', icon='icon.ico', target_name='gestao-simples.exe'),
]

options = {
    'build_exe': {
        'packages': [
            'pandas',
            'streamlit',
            'streamlit_date_picker',
            'schedule',
            'bs4',
            'cv2',
            'sqlalchemy',
            'urllib3',
            'pyzbar',
            'pyarrow',
            'pymysql',
            'selenium',
            'webdriver_manager',
            'dotenv',
            'pwdlib',
            'jwt',
            'zoneinfo',
        ],
        'includes': ['streamlit.runtime.scriptrunner.magic_funcs',],
        'include_files': [
            ('gestao_simples/.env', 'gestao_simples/.env'),
            ('gestao_simples/', 'gestao_simples/'),
            ('stop_server.bat', 'stop_server.bat'),
            ('icon.ico', 'icon.ico'),
            # outras pastas adicionais se necessário
        ],
        'optimize': 2,
        #'include_msvcr': True,
    }
}

setup(
    name='gestao-simples',
    version='0.1.1',
    description='Sistema de gestão simplificado',
    executables=executables,
    options=options,
)

# Copia o streamlit_date_picker e pyarrow.libs para o diretório de build
import shutil
from pathlib import Path

build_dir = Path('build/exe.win-amd64-3.11')
for lib in ['streamlit_date_picker', 'pyarrow.libs']:
    source = Path(f'.venv/Lib/site-packages/{lib}')
    dest = build_dir / 'lib' / lib
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    print(f'Cópia {source} para {dest}')