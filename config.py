import os
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime # Importado para o COPYRIGHT_NOTICE

# --- Caminhos Base ---
# Resolve o caminho base do projeto (onde este arquivo config.py está)
# Útil se o script for executado de um diretório diferente.
try:
    # Se estiver rodando como um script ou executável PyInstaller
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        BASE_DIR = Path(sys._MEIPASS) # Dentro do bundle PyInstaller
    else:
        BASE_DIR = Path(__file__).resolve().parent # Rodando como script .py
except NameError:
    # Fallback se __file__ não estiver definido (ex: alguns ambientes interativos)
    BASE_DIR = Path.cwd()

# ASSETS_DIR é definido no nível do módulo, usando BASE_DIR
ASSETS_DIR = BASE_DIR / 'assets'

# --- Configuração de Logging ---
def setup_logging(log_dir_base: Path, app_name_safe: str) -> logging.Logger:
    """Configura o logging para a aplicação."""
    log_dir = log_dir_base / app_name_safe / "Logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{app_name_safe.lower()}.log"
    except OSError: # Fallback para o diretório do script se o diretório AppData não puder ser criado
        log_dir = BASE_DIR / "logs_fallback"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{app_name_safe.lower()}_fallback.log"
        print(f"AVISO: Não foi possível criar o diretório de log padrão. Usando: {log_file}")

    _logger = logging.getLogger(app_name_safe)
    _logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    # Handler para console (útil para desenvolvimento)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    return _logger

# --- Verificação de Pillow (PIL) ---
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    # O logger pode não estar pronto aqui se houver erro antes da sua inicialização
    # print("AVISO: Biblioteca Pillow (PIL) não está instalada. Funcionalidade de imagens será limitada.")


class Config:
    APP_NAME = "AgendaCompPro"
    APP_NAME_SAFE = "AgendaComp" # Para nomes de diretório
    VERSION = "1.0.0" # Atualize conforme necessário

    # --- Informações do Autor (Preencha com seus dados) ---
    AUTHOR_NAME = "Claudeir de Souza Alves"
    AUTHOR_EMAIL = "claudeir@sicoob.com.br"  # Opcional, pode deixar ""
    # COPYRIGHT_NOTICE é construído usando datetime e AUTHOR_NAME
    # Garantindo que AUTHOR_NAME seja definido antes de ser usado.
    # Para evitar problemas com a ordem de definição, podemos definir após a classe ou como propriedade.
    # Por simplicidade, vamos definir aqui, mas certifique-se que AUTHOR_NAME já tem seu valor.
    COPYRIGHT_NOTICE = f"© {datetime.now().year} {AUTHOR_NAME}"


    # --- Caminhos de Ícones (usando ASSETS_DIR do módulo) ---
    # Esses caminhos são relativos à pasta 'assets' que está na mesma pasta do config.py
    LOGO_PATH = ASSETS_DIR / "logo.png"
    ICON_PATH = ASSETS_DIR / "agenda.ico" # Ícone principal da aplicação

    # Ícones para botões e menus
    ICON_NEW = ASSETS_DIR / "new_task.ico"
    ICON_EDIT = ASSETS_DIR / "edit_task.ico"
    ICON_DELETE = ASSETS_DIR / "delete_task.ico"
    ICON_COMPLETE = ASSETS_DIR / "complete_task.ico"
    ICON_REOPEN = ASSETS_DIR / "reopen_task.ico"
    ICON_USER = ASSETS_DIR / "user_manage.ico"
    ICON_REPORT = ASSETS_DIR / "report.ico"
    ICON_REFRESH = ASSETS_DIR / "refresh.ico"
    ICON_EXIT = ASSETS_DIR / "exit.ico"
    ICON_ABOUT = ASSETS_DIR / "about.ico"
    ICON_HELP = ASSETS_DIR / "help.ico"
    ICON_LOGIN = ASSETS_DIR / "login_key.ico"
    ICON_RESTORE = ASSETS_DIR / "restore.ico" # Ícone para a função de restaurar

    # --- Caminhos de Diretórios de Dados ---
    # Tenta usar o diretório AppData do usuário; se não conseguir, usa um fallback.
    try:
        DATA_PARENT_DIR = Path(os.getenv("APPDATA", BASE_DIR)) # APPDATA é mais comum no Windows
        if not os.access(DATA_PARENT_DIR, os.W_OK): # Verifica permissão de escrita
            raise OSError("Sem permissão de escrita no diretório APPDATA.")
        DATA_DIR = DATA_PARENT_DIR / APP_NAME_SAFE
    except Exception: # Se APPDATA não estiver definido ou não for acessível
        DATA_DIR = BASE_DIR / f"{APP_NAME_SAFE}_data" # Fallback para subpasta no diretório do app

    LOG_DIR = DATA_DIR / "Logs" # Logs agora dentro da pasta de dados principal
    BACKUP_DIR = DATA_DIR / "Backups"
    REPORTS_DIR = DATA_DIR / "Reports"

    USERS_FILE = DATA_DIR / 'users.json'
    TASKS_FILE = DATA_DIR / 'tasks.json'

    @classmethod
    def setup_dirs(cls):
        """Cria os diretórios necessários se não existirem."""
        try:
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
            cls.LOG_DIR.mkdir(parents=True, exist_ok=True) # Log dir é configurado no setup_logging
            cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            ASSETS_DIR.mkdir(parents=True, exist_ok=True) # Garante que a pasta assets existe
            
            logger.info(f"Diretórios de dados configurados/verificados em: {cls.DATA_DIR}")
            logger.info(f"Diretório de assets configurado/verificado em: {ASSETS_DIR}")
        except Exception as e:
            # Se o logger ainda não estiver configurado, esta mensagem pode não aparecer no arquivo de log
            print(f"ERRO CRÍTICO ao configurar diretórios: {e}. Verifique as permissões.")
            # O logger pode ser configurado após esta chamada, então este log é importante no console
            if 'logger' in globals(): # Verifica se o logger global já foi definido
                logger.critical(f"Erro fatal ao configurar diretórios: {e}", exc_info=True)
            sys.exit(f"Erro fatal ao configurar diretórios: {e}")

# --- Inicializa o Logger ---
# É importante que o logger seja configurado após a definição de LOG_DIR
# e que setup_dirs seja chamado antes para garantir que LOG_DIR exista.
# No entanto, setup_dirs usa o logger. Para evitar problemas de ordem,
# passamos DATA_DIR para setup_logging.
logger = setup_logging(Config.DATA_DIR, Config.APP_NAME_SAFE)

# --- Chama a Configuração de Diretórios ---
# Isso deve ser feito após a definição da classe Config e do logger.
try:
    Config.setup_dirs()
except Exception as e:
    # Esta mensagem aparecerá no console se setup_dirs falhar criticamente antes do logger estar fully up.
    print(f"Falha crítica na inicialização dos diretórios em config.py: {e}")
    # O sys.exit já está dentro de setup_dirs em caso de falha lá.

if not HAS_PIL: # Agora o logger existe
    logger.warning("Biblioteca Pillow (PIL) não está instalada. `pip install Pillow`. Funcionalidade de imagens (como logo e ícones) será limitada ou ausente.")

logger.info(f"{Config.APP_NAME} v{Config.VERSION} - Configurações carregadas.")