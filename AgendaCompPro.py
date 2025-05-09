import os
import sys
import tkinter as tk
from tkinter import messagebox

# === BLOCO DE SUPORTE AO PyInstaller ===
def resource_path(relative_path):
    """Retorna caminho absoluto para recursos, compatível com PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === IMPORTAÇÃO DE CONFIG E LOG ===
try:
    from config import logger, Config
except ImportError as e:
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
    logger = logging.getLogger("AgendaComp_Fallback")
    logger.critical(f"Falha crítica ao importar 'config': {e}", exc_info=True)
    try:
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror("Erro Crítico de Inicialização", f"Erro: {e}")
        root_err.destroy()
    except Exception as tk_e:
        logger.error(f"Falha ao exibir erro com Tkinter: {tk_e}")
    sys.exit(1)

# === IMPORTAÇÃO DA JANELA DE LOGIN ===
try:
    from gui.login_window import LoginWindow
except ImportError as e:
    logger.critical(f"Falha ao importar módulos da aplicação: {e}", exc_info=True)
    try:
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror(
            f"Erro Crítico em {Config.APP_NAME}",
            f"Erro ao carregar componentes da aplicação.\nErro: {e}"
        )
        root_err.destroy()
    except Exception as tk_e:
        logger.error(f"Falha ao exibir erro com Tkinter: {tk_e}")
    sys.exit(1)

# === FUNÇÃO PÚBLICA PARA SER CHAMADA PELO main.py ===
def iniciar_app():
    try:
        logger.info(f"Iniciando aplicação {Config.APP_NAME} v{Config.VERSION}")
        LoginWindow()
        logger.info(f"Aplicação {Config.APP_NAME} encerrada normalmente.")
    except Exception as e:
        logger.critical(f"Erro fatal na execução principal: {e}", exc_info=True)
        try:
            root_fatal = tk.Tk()
            root_fatal.withdraw()
            messagebox.showerror(
                f"Erro Fatal em {Config.APP_NAME}",
                f"Ocorreu um erro crítico:\n{e}\nVerifique o log."
            )
            root_fatal.destroy()
        except Exception as tk_e:
            logger.error(f"Falha ao exibir erro fatal com Tkinter: {tk_e}")
        sys.exit(1)
