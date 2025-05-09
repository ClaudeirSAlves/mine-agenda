import os
import sys
import tkinter as tk  # Necessário para messagebox em caso de erro fatal antes da GUI
from tkinter import messagebox

# === NOVO BLOCO: suporte a recursos empacotados com PyInstaller ===
def resource_path(relative_path):
    """Retorna caminho absoluto para recursos, compatível com PyInstaller."""
    try:
        base_path = sys._MEIPASS  # Diretório temporário do PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")  # Durante execução normal (.py)
    return os.path.join(base_path, relative_path)

# === FIM DO BLOCO DE AJUSTE ===

# Tenta importar a configuração primeiro para configurar o logging o mais cedo possível
try:
    from config import logger, Config  # Config para APP_NAME em erro fatal
except ImportError as e:
    # Fallback de logging se config.py falhar ao importar
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
    logger = logging.getLogger("AgendaComp_Fallback")
    logger.critical(f"Falha crítica ao importar 'config'. Verifique a estrutura do projeto e PYTHONPATH: {e}", exc_info=True)
    # Exibir erro visualmente se tkinter puder ser importado
    try:
        root_err = tk.Tk()
        root_err.withdraw()  # Oculta a janela principal do Tkinter
        messagebox.showerror(
            "Erro Crítico de Inicialização",
            f"Não foi possível carregar as configurações da aplicação (config.py).\n"
            f"Verifique o console para mais detalhes.\nErro: {e}"
        )
        root_err.destroy()
    except Exception as tk_e:
        logger.error(f"Não foi possível mostrar erro com Tkinter: {tk_e}")
    sys.exit(1)

# Importar o restante após o logging estar configurado
try:
    from gui.login_window import LoginWindow
    # from services import UserService, TaskService  # Para debug futuro
except ImportError as e:
    logger.critical(f"Falha crítica ao importar módulos da aplicação (gui ou services): {e}", exc_info=True)
    try:
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror(
            f"Erro Crítico em {Config.APP_NAME if 'Config' in globals() else 'Aplicação'}",
            f"Erro ao carregar componentes da aplicação.\nVerifique o console.\nErro: {e}"
        )
        root_err.destroy()
    except Exception as tk_e:
        logger.error(f"Não foi possível mostrar erro com Tkinter: {tk_e}")
    sys.exit(1)


if __name__ == '__main__':
    try:
        logger.info(f"Iniciando aplicação {Config.APP_NAME} v{Config.VERSION}")

        # Exemplo de uso do resource_path em outro lugar no seu código:
        # icon_path = resource_path("assets/agenda.ico")
        # image_path = resource_path("assets/logo.png")

        LoginWindow()

        logger.info(f"Aplicação {Config.APP_NAME} encerrada normalmente.")

    except Exception as e:
        logger.critical(f"Erro fatal não tratado na execução principal: {str(e)}", exc_info=True)
        try:
            root_fatal = tk.Tk()
            root_fatal.withdraw()
            messagebox.showerror(
                f"Erro Fatal em {Config.APP_NAME}",
                f"Ocorreu um erro crítico e inesperado:\n{str(e)}\n\n"
                "A aplicação será encerrada. Verifique o arquivo de log para detalhes."
            )
            root_fatal.destroy()
        except Exception as tk_e_fatal:
            logger.error(f"Não foi possível mostrar erro fatal com Tkinter: {tk_e_fatal}")
        sys.exit(1)
