import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List
import shutil 

from config import Config, logger 

class UserService: # Sem alterações na UserService
    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16).hex() 
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest() + ':' + salt

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        if ':' not in stored_hash:
            logger.warning("Tentativa de verificação de senha com hash malformado (sem salt).")
            return False 
        hash_part, salt = stored_hash.split(':', 1)
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest() == hash_part

    @staticmethod
    def load_users() -> Dict[str, Dict]:
        try:
            if not Config.USERS_FILE.exists():
                logger.info(f"Arquivo de usuários não encontrado em {Config.USERS_FILE}. Criando com admin padrão.")
                default_admin_username = 'admin'
                default_admin_password = 'admin123'
                default_admin_data = {
                    default_admin_username: {
                        'password_hash': UserService.hash_password(default_admin_password),
                        'level': 'admin',
                        'email': 'admin@example.com'
                    }
                }
                UserService.save_users(default_admin_data)
                logger.info(f"Usuário padrão '{default_admin_username}' com senha '{default_admin_password}' criado.")
                return default_admin_data
            
            with open(Config.USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
                logger.info(f"Usuários carregados de {Config.USERS_FILE}: {len(users)} registros.")
                return users
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON do arquivo de usuários {Config.USERS_FILE}: {e}. Arquivo pode estar corrompido.")
            return {} 
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar usuários de {Config.USERS_FILE}: {e}", exc_info=True)
            return {}

    @staticmethod
    def save_users(users: Dict[str, Dict]):
        try:
            Config.DATA_DIR.mkdir(parents=True, exist_ok=True) 
            
            if Config.USERS_FILE.exists():
                Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True) 
                backup_file_path = Config.BACKUP_DIR / f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(Config.USERS_FILE, backup_file_path) 
                logger.info(f"Backup do arquivo de usuários criado em: {backup_file_path}")
            
            with open(Config.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
            logger.info(f"Usuários salvos com sucesso em {Config.USERS_FILE}")
        except Exception as e:
            logger.error(f"Erro ao salvar usuários em {Config.USERS_FILE}: {e}", exc_info=True)
            raise 

class TaskService:
    @staticmethod
    def load_tasks() -> List[Dict]:
        try:
            if not Config.TASKS_FILE.exists():
                logger.info(f"Arquivo de tarefas não encontrado em {Config.TASKS_FILE}. Criando arquivo vazio.")
                with open(Config.TASKS_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f) 
                return []
            
            with open(Config.TASKS_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                logger.info(f"Tarefas carregadas de {Config.TASKS_FILE}: {len(tasks)} registros.")
                return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON do arquivo de tarefas {Config.TASKS_FILE}: {e}. Arquivo pode estar corrompido.")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar tarefas de {Config.TASKS_FILE}: {e}", exc_info=True)
            return []

    @staticmethod
    def save_tasks(tasks: List[Dict]):
        try:
            Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

            if Config.TASKS_FILE.exists():
                Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                backup_file_path = Config.BACKUP_DIR / f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(Config.TASKS_FILE, backup_file_path)
                logger.info(f"Backup do arquivo de tarefas criado em: {backup_file_path}")

            with open(Config.TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)
            logger.info(f"Tarefas salvas com sucesso em {Config.TASKS_FILE}")
        except Exception as e:
            logger.error(f"Erro ao salvar tarefas em {Config.TASKS_FILE}: {e}", exc_info=True)
            raise
            
    # NOVO MÉTODO para gerar o próximo ID de tarefa incremental
    @staticmethod
    def get_next_task_id() -> str:
        """Gera o próximo ID numérico incremental para uma tarefa."""
        tasks_list_of_dicts = TaskService.load_tasks() # Carrega os dicts crus do JSON
        if not tasks_list_of_dicts:
            return "1" # Começa do 1 se não houver tarefas
        
        max_int_id = 0
        for task_dict in tasks_list_of_dicts:
            task_id_str = str(task_dict.get('task_id', "0")) # Converte para string para segurança
            if task_id_str.isdigit(): # Verifica se o ID é uma string de dígitos
                try:
                    current_id_int = int(task_id_str)
                    if current_id_int > max_int_id:
                        max_int_id = current_id_int
                except ValueError:
                    # Ignora IDs que não são puramente numéricos (como UUIDs antigos)
                    # para o cálculo do próximo ID incremental.
                    pass 
        return str(max_int_id + 1)

# --- Adições Automáticas ---

    @staticmethod
    def save_users(users: Dict[str, Dict]) -> None:
        try:
            with open(Config.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=4, ensure_ascii=False)
            logger.info(f"Usuários salvos com sucesso em {Config.USERS_FILE}.")
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")


class TaskService:
    @staticmethod
    def load_tasks() -> List[Dict]:
        if not Config.TASKS_FILE.exists():
            logger.info(f"Arquivo de tarefas não encontrado em {Config.TASKS_FILE}. Criando vazio.")
            return []
        try:
            with open(Config.TASKS_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                logger.info(f"Tarefas carregadas: {len(tasks)} registros.")
                return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON de tarefas: {e}")
            return []

    @staticmethod
    def save_tasks(tasks: List[Dict]) -> None:
        try:
            with open(Config.TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)
            logger.info(f"{len(tasks)} tarefas salvas em {Config.TASKS_FILE}.")
        except Exception as e:
            logger.error(f"Erro ao salvar tarefas: {e}")

    @staticmethod
    def add_task(task_data: Dict) -> None:
        tasks = TaskService.load_tasks()
        tasks.append(task_data)
        TaskService.save_tasks(tasks)
        logger.info(f"Tarefa adicionada: {task_data.get('description', '')}")

    @staticmethod
    def remove_task(task_id: str) -> None:
        tasks = TaskService.load_tasks()
        tasks = [task for task in tasks if task.get('task_id') != task_id]
        TaskService.save_tasks(tasks)
        logger.info(f"Tarefa removida: {task_id}")

    @staticmethod
    def complete_task(task_id: str, completed_by: str) -> None:
        tasks = TaskService.load_tasks()
        for task in tasks:
            if task.get('task_id') == task_id:
                task['is_completed'] = True
                task['completed_at'] = datetime.now().isoformat()
                task['completed_by'] = completed_by
                break
        TaskService.save_tasks(tasks)
        logger.info(f"Tarefa marcada como concluída: {task_id} por {completed_by}")


    @staticmethod
    def get_next_task_id() -> str:
        tasks = TaskService.load_tasks()
        if not tasks:
            return "1"
        try:
            max_id = max(int(task.get("task_id", 0)) for task in tasks if str(task.get("task_id", "0")).isdigit())
            return str(max_id + 1)
        except Exception as e:
            logger.warning(f"Falha ao gerar próximo task_id: {e}")
            return str(uuid.uuid4())  # fallback seguro
