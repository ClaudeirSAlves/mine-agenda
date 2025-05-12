import os
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# --- Caminhos Base ---
# Resolve o caminho base do projeto (onde este arquivo config.py está)
try:
    # Se estiver rodando como um script ou executável PyInstaller
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        BASE_DIR = Path(sys._MEIPASS)  # Dentro do bundle PyInstaller
    else:
        BASE_DIR = Path(__file__).resolve().parent  # Rodando como script .py
except NameError:
    # Fallback se __file__ não estiver definido (ex: alguns ambientes interativos)
    BASE_DIR = Path.cwd()

# ASSETS_DIR é relativo ao BASE_DIR (onde o config.py ou o executável está)
ASSETS_DIR = BASE_DIR / 'assets'

# --- Verificação de Pillow (PIL) ---
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    # Um print aqui é útil se o logger ainda não estiver configurado
    # print("AVISO INICIAL: Biblioteca Pillow (PIL) não está instalada. Funcionalidade de imagens será limitada.")


class Config:
    APP_NAME = "AgendaCompPro"
    APP_NAME_SAFE = "AgendaComp"  # Para nomes de diretório seguros
    VERSION = "1.0.0"  # Atualize conforme necessário

    # --- Informações do Autor ---
    AUTHOR_NAME = "Claudeir de Souza Alves"
    AUTHOR_EMAIL = "claudeir@sicoob.com.br"
    COPYRIGHT_NOTICE = f"© {datetime.now().year} {AUTHOR_NAME if AUTHOR_NAME else APP_NAME}"

    # --- Caminhos de Diretórios de Dados ---
    # Tenta usar o diretório AppData do usuário; se não conseguir, usa um fallback.
    try:
        # Tenta usar um diretório de dados específico do aplicativo no APPDATA ou local similar.
        data_parent_candidate = Path(os.getenv("APPDATA", os.getenv("LOCALAPPDATA", os.getenv("HOME", BASE_DIR))))
        if os.access(str(data_parent_candidate), os.W_OK): # Verifica permissão de escrita
             # Adiciona o nome da aplicação ao caminho pai para isolar os dados
            DATA_DIR_BASE_FOR_APP = data_parent_candidate / APP_NAME_SAFE
        else: # Fallback se não houver permissão de escrita no diretório pai preferencial
            raise OSError(f"Sem permissão de escrita no diretório de dados preferencial: {data_parent_candidate}")
    except Exception as e_path:
        print(f"AVISO ao definir DATA_DIR: {e_path}. Usando fallback no diretório da aplicação.")
        DATA_DIR_BASE_FOR_APP = BASE_DIR / f"{APP_NAME_SAFE}_data_fallback"

    # Diretórios específicos da aplicação
    DATA_DIR = DATA_DIR_BASE_FOR_APP # Diretório principal de dados da aplicação
    LOG_DIR = DATA_DIR / "Logs"
    BACKUP_DIR = DATA_DIR / "Backups"
    REPORTS_DIR = DATA_DIR / "Reports"

    # Arquivos de dados
    USERS_FILE = DATA_DIR / 'users.json'
    TASKS_FILE = DATA_DIR / 'tasks.json'

    # --- Caminhos de Ícones (usando ASSETS_DIR) ---
    # ASSETS_DIR deve existir no mesmo nível do executável/script principal
    # ou ser incluído corretamente pelo PyInstaller.
    LOGO_PATH = ASSETS_DIR / "logo.png"
    ICON_PATH = ASSETS_DIR / "agenda.ico"  # Ícone principal da aplicação

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
    ICON_RESTORE = ASSETS_DIR / "restore.ico"
    # Adicione outros ícones conforme necessário, por exemplo:
    # ICON_CHANGE_PASSWORD = ASSETS_DIR / "change_password.ico"

    @classmethod
    def setup_dirs(cls):
        """Cria os diretórios necessários se não existirem."""
        global logger # Para usar o logger que será definido abaixo
        try:
            # Garante que ASSETS_DIR exista ou seja logado se não existir (para debug)
            if not ASSETS_DIR.exists():
                # Não tenta criar, pois assets devem ser distribuídos com a app.
                # Apenas loga um aviso se o logger já estiver disponível.
                if 'logger' in globals() and logger:
                    logger.warning(f"Diretório de assets '{ASSETS_DIR}' não encontrado. Ícones e logo podem estar ausentes.")
                else: # Logger ainda não disponível
                    print(f"AVISO: Diretório de assets '{ASSETS_DIR}' não encontrado.")
            # else: # Logger pode não estar pronto
            #     print(f"INFO: Diretório de assets verificado em: {ASSETS_DIR}")


            # Cria diretórios de dados
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
            # cls.LOG_DIR.mkdir(parents=True, exist_ok=True) # Log dir é criado dentro de setup_logging
            cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

            if 'logger' in globals() and logger: # Verifica se o logger global já foi definido
                logger.info(f"Diretórios de dados configurados/verificados em: {cls.DATA_DIR}")
            else: # Logger ainda não disponível
                print(f"INFO: Diretórios de dados configurados/verificados em: {cls.DATA_DIR}")

        except Exception as e:
            # Se o logger ainda não estiver configurado, esta mensagem pode não aparecer no arquivo de log
            critical_error_msg = f"ERRO CRÍTICO ao configurar diretórios ({cls.DATA_DIR}): {e}. Verifique as permissões."
            print(critical_error_msg)
            if 'logger' in globals() and logger:
                logger.critical(critical_error_msg, exc_info=True)
            sys.exit(critical_error_msg)


# --- Configuração de Logging ---
# Esta função é chamada antes da inicialização completa do logger global,
# mas o logger retornado por ela será o logger global.
def setup_logging(log_dir_path: Path, app_name_safe_for_logger: str) -> logging.Logger:
    """Configura o logging para a aplicação."""
    # log_dir_path já é Config.LOG_DIR
    try:
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_file = log_dir_path / f"{app_name_safe_for_logger.lower()}.log"
    except OSError as e_log_path:
        # Fallback para o diretório base do script se o diretório de logs padrão não puder ser criado
        print(f"AVISO: Não foi possível criar/acessar o diretório de log padrão {log_dir_path}: {e_log_path}.")
        log_dir_fallback = BASE_DIR / "logs_fallback"
        try:
            log_dir_fallback.mkdir(parents=True, exist_ok=True)
            log_file = log_dir_fallback / f"{app_name_safe_for_logger.lower()}_fallback.log"
            print(f"Usando diretório de log fallback: {log_file}")
        except Exception as e_fallback:
            print(f"ERRO CRÍTICO: Não foi possível criar diretório de log fallback {log_dir_fallback}: {e_fallback}. Logging desabilitado para arquivo.")
            log_file = None # Desabilita log em arquivo

    # Cria o logger com o nome seguro da aplicação
    _logger = logging.getLogger(app_name_safe_for_logger)
    _logger.setLevel(logging.INFO) # Nível padrão de logging

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para arquivo com rotação (se log_file foi definido)
    if log_file:
        try:
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)
        except Exception as e_fh:
            print(f"ERRO ao configurar file handler para logs em {log_file}: {e_fh}")


    # Handler para console (útil para desenvolvimento e erros críticos iniciais)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    return _logger

# --- Inicializa o Logger Global ---
# O logger é configurado usando Config.LOG_DIR e Config.APP_NAME_SAFE.
# Config.LOG_DIR em si depende de Config.DATA_DIR.
# Config.DATA_DIR é definido na classe Config.
# A ordem é: Definição da classe Config -> Chamada de setup_logging com caminhos de Config -> Definição do logger global.
logger = setup_logging(Config.LOG_DIR, Config.APP_NAME_SAFE)


# --- Chama a Configuração de Diretórios ---
# Isso deve ser feito após a definição da classe Config e APÓS a inicialização do logger global,
# para que setup_dirs possa usar o logger.
try:
    Config.setup_dirs()
except Exception as e:
    # Esta mensagem aparecerá no console se setup_dirs falhar criticamente.
    # O sys.exit já está dentro de setup_dirs em caso de falha lá.
    logger.critical(f"Falha crítica não capturada na inicialização dos diretórios em config.py: {e}", exc_info=True)
    sys.exit(f"Erro fatal não capturado ao configurar diretórios: {e}")


# --- Aviso Final sobre Pillow (PIL) ---
if not HAS_PIL: # Agora o logger existe e está configurado
    logger.warning(
        "Biblioteca Pillow (PIL) não está instalada. "
        "Execute `pip install Pillow` para habilitar funcionalidades de imagem (logos, ícones)."
        " As imagens podem não ser exibidas corretamente."
    )

logger.info(f"--- {Config.APP_NAME} v{Config.VERSION} --- Configurações carregadas. Logger inicializado. ---")
logger.info(f"Diretório base da aplicação (BASE_DIR): {BASE_DIR}")
logger.info(f"Diretório de assets (ASSETS_DIR): {ASSETS_DIR}")
logger.info(f"Diretório principal de dados (Config.DATA_DIR): {Config.DATA_DIR}")
logger.info(f"Diretório de logs (Config.LOG_DIR): {Config.LOG_DIR}")