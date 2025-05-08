import uuid
from datetime import datetime
from typing import Dict, Optional

class User: # Sem alterações na classe User
    def __init__(self, username: str, password_hash: str, level: str, email: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.level = level 
        self.email = email

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        return cls(
            username=data.get('username',''),
            password_hash=data.get('password_hash',''),
            level=data.get('level', 'operador'),
            email=data.get('email', '')
        )

    def to_dict(self) -> Dict:
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'level': self.level,
            'email': self.email
        }

class Task:
    def __init__(self, description: str, user: str, 
                 task_id: str, # task_id agora é obrigatório e fornecido externamente
                 is_completed: bool = False,
                 created_at: Optional[str] = None, 
                 completed_at: Optional[str] = None,
                 completed_by: Optional[str] = None, 
                 priority: int = 1, 
                 category: str = ""):
        # O ID da tarefa (task_id) agora deve ser fornecido ao criar a tarefa.
        # Não há mais geração automática de UUID aqui.
        self.task_id = task_id 
        self.description = description
        self.user = user 
        self.is_completed = is_completed
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at 
        self.completed_by = completed_by 
        self.priority = priority
        self.category = category

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        # Garante que task_id seja lido, mesmo que seja None no JSON (o que não deveria acontecer para tarefas salvas)
        task_id_from_data = data.get('task_id')
        if task_id_from_data is None:
            # Isso pode acontecer se um dev tentar criar um Task a partir de um dict sem task_id
            # Para tarefas carregadas do JSON, o task_id deve existir.
            # Se quisermos ser ultra-robustos, poderíamos gerar um UUID aqui como fallback, mas
            # a lógica de ID incremental deve garantir que ele seja fornecido.
            # Por ora, vamos assumir que quem chama from_dict de dados de JSON sempre terá um task_id.
            # Se não, pode-se levantar um erro ou logar.
            # Para o caso de ID incremental, o serviço deve garantir a passagem do ID.
            pass # O __init__ receberá None e o serviço deverá ter fornecido um ID.

        return cls(
            task_id=str(task_id_from_data) if task_id_from_data is not None else str(uuid.uuid4()), # Garante que seja string e fallback
            description=data.get('description',''),
            user=data.get('user',''), 
            is_completed=data.get('is_completed', False),
            created_at=data.get('created_at'),
            completed_at=data.get('completed_at'),
            completed_by=data.get('completed_by'), 
            priority=data.get('priority', 1),
            category=data.get('category', '')
        )

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id, # task_id é string
            'description': self.description,
            'user': self.user, 
            'is_completed': self.is_completed,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'completed_by': self.completed_by, 
            'priority': self.priority,
            'category': self.category
        }