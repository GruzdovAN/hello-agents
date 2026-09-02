"""Определения моделей данных"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ContentLevel(Enum):
    """Уровень контента"""
    TOPIC = 1      # уровень подтемы
    SECTION = 2    # уровень секции
    DETAIL = 3     # уровень деталей


@dataclass
class ContentNode:
    """Узел дерева контента"""
    id: str                                    # уникальный ID узла
    title: str                                 # заголовок узла
    level: ContentLevel                        # уровень контента
    description: str                           # описание узла
    content: Optional[str] = None              # контент (markdown)
    children: List['ContentNode'] = field(default_factory=list)  # дочерние узлы
    metadata: Dict[str, Any] = field(default_factory=dict)       # метаданные
    revision_history: List[Dict[str, Any]] = field(default_factory=list)  # история правок
    
    def add_child(self, child: 'ContentNode'):
        """Добавить дочерний узел"""
        self.children.append(child)
    
    def get_all_nodes(self) -> List['ContentNode']:
        """Все узлы (DFS)"""
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes
    
    def count_words(self) -> int:
        """Сумма слов узла и детей"""
        total = len(self.content) if self.content else 0
        for child in self.children:
            total += child.count_words()
        return total


@dataclass  
class ReviewResult:
    """Результат ревью"""
    score: int                                 # сумма (0-100)
    grade: str                                 # оценка
    dimension_scores: Dict[str, int]           # баллы по измерениям
    detailed_feedback: Dict[str, Any]          # детальная обратная связь
    revision_plan: Dict[str, Any]              # план правок
    needs_revision: bool                       # нужна ли правка
    estimated_effort: str = ""                 # оценка трудозатрат
    reviewer_notes: str = ""                   # заметки ревьюера
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewResult':
        """Создать ReviewResult из dict"""
        return cls(
            score=data.get('score', 0),
            grade=data.get('grade', 'неизвестно'),
            dimension_scores=data.get('dimension_scores', {}),
            detailed_feedback=data.get('detailed_feedback', {}),
            revision_plan=data.get('revision_plan', {}),
            needs_revision=data.get('needs_revision', False),
            estimated_effort=data.get('estimated_revision_effort', ''),
            reviewer_notes=data.get('reviewer_notes', '')
        )


@dataclass
class ColumnPlan:
    """План колонки"""
    column_title: str                          # заголовок колонки
    column_description: str                    # описание колонки
    target_audience: str                       # целевая аудитория
    topics: List[Dict[str, Any]]               # список подтем
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnPlan':
        """Создать ColumnPlan из dict"""
        return cls(
            column_title=data.get('column_title', ''),
            column_description=data.get('column_description', ''),
            target_audience=data.get('target_audience', ''),
            topics=data.get('topics', [])
        )
    
    def get_topic_count(self) -> int:
        """Число подтем"""
        return len(self.topics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в dict (кэш)"""
        return {
            'column_title': self.column_title,
            'column_description': self.column_description,
            'target_audience': self.target_audience,
            'topics': self.topics
        }
