# services.py
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List
import shutil

# Importações do projeto
from config import Config, logger
# models.py não é diretamente usado aqui para manipulação, pois os serviços lidam com dicionários
# que são então convertidos para/de objetos Task na camada da GUI (ex: MainWindow).

class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Gera um hash seguro para a senha com um salt."""
        salt = os.urandom(16).hex()
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest() + ':' + salt

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        """Verifica a senha fornecida contra o hash armazenado."""
        if ':' not in stored_hash:
            logger.warning("Tentativa de verificação de senha com hash malformado (sem salt).")
            return False
        hash_part, salt = stored_hash.split(':', 1)
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest() == hash_part

    @staticmethod
    def load_users() -> Dict[str, Dict]:
        """Carrega os dados dos usuários do arquivo JSON. Cria um usuário admin padrão se o arquivo não existir."""
        try:
            if not Config.USERS_FILE.exists():
                logger.info(f"Arquivo de usuários não encontrado em {Config.USERS_FILE}. Criando com admin padrão.")
                default_admin_username = 'admin'
                default_admin_password = 'admin123'
                default_admin_data = {
                    default_admin_username: {
                        'password_hash': UserService.hash_password(default_admin_password),
                        'level': 'admin',
                        'email': 'admin@example.com' # Email padrão para admin
                    }
                }
                UserService.save_users(default_admin_data) # Salva para criar o arquivo
                logger.info(f"Usuário padrão '{default_admin_username}' com senha inicial '{default_admin_password}' criado.")
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
    def save_users(users: Dict[str, Dict]) -> None:
        """Salva os dados dos usuários no arquivo JSON, criando um backup antes de salvar."""
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
        """Carrega as tarefas do arquivo JSON. Cria um arquivo vazio se não existir."""
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
    def save_tasks(tasks: List[Dict]) -> None:
        """Salva a lista de tarefas no arquivo JSON, criando um backup antes de salvar."""
        try:
            Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

            if Config.TASKS_FILE.exists():
                Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                backup_file_path = Config.BACKUP_DIR / f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(Config.TASKS_FILE, backup_file_path)
                logger.info(f"Backup do arquivo de tarefas criado em: {backup_file_path}")

            with open(Config.TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)
            logger.info(f"{len(tasks)} tarefas salvas com sucesso em {Config.TASKS_FILE}")
        except Exception as e:
            logger.error(f"Erro ao salvar tarefas em {Config.TASKS_FILE}: {e}", exc_info=True)
            raise

    @staticmethod
    def get_next_task_id() -> str:
        """Gera o próximo ID numérico incremental para uma tarefa."""
        tasks_list_of_dicts = TaskService.load_tasks()
        if not tasks_list_of_dicts:
            return "1"

        max_int_id = 0
        for task_dict in tasks_list_of_dicts:
            task_id_str = str(task_dict.get('task_id', "0"))
            if task_id_str.isdigit():
                try:
                    current_id_int = int(task_id_str)
                    if current_id_int > max_int_id:
                        max_int_id = current_id_int
                except ValueError:
                    logger.warning(f"ID de tarefa '{task_id_str}' é numérico mas falhou na conversão para int. Ignorando.")
                    pass
            else:
                logger.debug(f"ID de tarefa não numérico '{task_id_str}' encontrado e ignorado para cálculo de ID incremental.")
        return str(max_int_id + 1)

    @staticmethod
    def add_task(task_data: Dict) -> None:
        """Adiciona uma nova tarefa (como dicionário) à lista e salva."""
        tasks = TaskService.load_tasks()
        tasks.append(task_data)
        TaskService.save_tasks(tasks)
        logger.info(f"Tarefa '{task_data.get('task_id')}' adicionada: {task_data.get('description', '')[:50]}...")

    @staticmethod
    def remove_task(task_id: str) -> None:
        """Remove uma tarefa da lista pelo seu ID e salva as alterações."""
        tasks = TaskService.load_tasks()
        tasks_before_removal = len(tasks)
        tasks = [task for task in tasks if task.get('task_id') != task_id]
        if len(tasks) < tasks_before_removal:
            TaskService.save_tasks(tasks)
            logger.info(f"Tarefa com ID '{task_id}' removida.")
        else:
            logger.warning(f"Tentativa de remover tarefa com ID '{task_id}', mas não foi encontrada.")

    @staticmethod
    def update_task(updated_task_data: Dict) -> bool:
        """
        Atualiza uma tarefa existente na lista. A tarefa é identificada pelo 'task_id'
        dentro do updated_task_data.
        Retorna True se a tarefa foi encontrada e atualizada, False caso contrário.
        """
        tasks = TaskService.load_tasks()
        task_id_to_update = updated_task_data.get('task_id')
        if not task_id_to_update:
            logger.error("Tentativa de atualizar tarefa sem task_id no dicionário.")
            return False

        updated = False
        for i, task_dict in enumerate(tasks): # Iterar sobre dicionários
            if task_dict.get('task_id') == task_id_to_update:
                tasks[i] = updated_task_data # Substitui o dicionário antigo pelo novo
                updated = True
                break
        
        if updated:
            TaskService.save_tasks(tasks)
            logger.info(f"Tarefa com ID '{task_id_to_update}' atualizada.")
            return True
        else:
            logger.warning(f"Tentativa de atualizar tarefa com ID '{task_id_to_update}', mas não foi encontrada.")
            return False

    @staticmethod
    def complete_task(task_id: str, completed_by: str) -> bool:
        """Marca uma tarefa como concluída."""
        tasks = TaskService.load_tasks()
        task_found = False
        for task_dict in tasks:
            if task_dict.get('task_id') == task_id:
                if task_dict.get('is_completed'):
                    logger.info(f"Tarefa '{task_id}' já estava marcada como concluída.")
                    return True

                task_dict['is_completed'] = True
                task_dict['completed_at'] = datetime.now().isoformat()
                task_dict['completed_by'] = completed_by
                task_found = True
                break
        
        if task_found:
            TaskService.save_tasks(tasks)
            logger.info(f"Tarefa '{task_id}' marcada como concluída por '{completed_by}'.")
            return True
        else:
            logger.warning(f"Tentativa de concluir tarefa com ID '{task_id}', mas não foi encontrada.")
            return False

    @staticmethod
    def reopen_task(task_id: str) -> bool:
        """Reabre uma tarefa que estava concluída."""
        tasks = TaskService.load_tasks()
        task_found = False
        for task_dict in tasks:
            if task_dict.get('task_id') == task_id:
                if not task_dict.get('is_completed'):
                    logger.info(f"Tarefa '{task_id}' já estava marcada como pendente/reaberta.")
                    return True

                task_dict['is_completed'] = False
                task_dict['completed_at'] = None
                task_dict['completed_by'] = None
                task_found = True
                break
        
        if task_found:
            TaskService.save_tasks(tasks)
            logger.info(f"Tarefa '{task_id}' reaberta.")
            return True
        else:
            logger.warning(f"Tentativa de reabrir tarefa com ID '{task_id}', mas não foi encontrada.")
            return False