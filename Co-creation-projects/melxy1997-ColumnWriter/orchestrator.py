"""Оркестрация системы в мультиагентном режиме"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from models import ContentNode, ContentLevel, ColumnPlan, ReviewResult
from agents import (
    PlannerAgent,
    WriterAgent,
    ReflectionWriterAgent,
    ReviewerAgent,
    RevisionAgent
)
from config import get_settings, get_word_count


class ColumnWriterOrchestrator:
    """
    Система написания колонок в мультиагентном режиме

    Архитектура:
    1. PlannerAgent → PlanAndSolveAgent (планирование)
    2. WriterAgent → ReActAgent (рассуждение и инструменты)
    3. ревью+правки → ReflectionAgent (саморефлексия)
    """
    
    def __init__(self, use_reflection_mode: bool = False):
        """
        Инициализация оркестратора

        Args:
            use_reflection_mode: режим ReflectionAgent
                - True: ReflectionAgent (авторевью)
                - False: ReActAgent + отдельный ревью
        """
        self.settings = get_settings()
        self.use_reflection_mode = use_reflection_mode
        
#Создаем каждого агента
        print("\n▸ Инициализация системы написания колонок...")
        print(f"   Режим: {'ReflectionAgent' if use_reflection_mode else 'ReActAgent + ревью'}")
        
        # Planner — PlanAndSolveAgent
        self.planner = PlannerAgent()
        
        # Writer — по режиму
        if use_reflection_mode:
            self.writer = ReflectionWriterAgent()
            print("   WriterAgent: ReflectionAgent (встроенный ревью)")
            self.reviewer = None
            self.revision_agent = None
        else:
            self.writer = WriterAgent(enable_search=self.settings.enable_search)
            print("   WriterAgent: ReActAgent (рассуждение-действие-поиск)")
            
            # Reviewer/Revision (только ReAct)
            if self.settings.enable_review:
                self.reviewer = ReviewerAgent()
                self.revision_agent = RevisionAgent()
                print(f"   ReviewerAgent: включён (порог: {self.settings.approval_threshold})")
                print(f"   RevisionAgent: включён (макс. правок: {self.settings.max_revisions})")
            else:
                self.reviewer = None
                self.revision_agent = None
                print("   ReviewerAgent: отключён")
        
# Статистика
        self.stats = {
            'total_generations': 0,
            'total_reviews': 0,
            'total_revisions': 0,
            'total_rewrites': 0,
            'approved_first_try': 0,
            'start_time': None,
            'end_time': None
        }
        
        print("▸ Инициализация завершена\n")
    
    def create_column(self, main_topic: str) -> Dict[str, Any]:
        """
        Создать полную колонку

        Args:
            main_topic: тема колонки

        Returns:
            dict с полной информацией о колонке
        """
        self.stats['start_time'] = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"▸ Создание колонки: {main_topic}")
        print(f"{'='*70}\n")
        
        # Шаг 1: планирование структуры (PlanAndSolveAgent)
        print("▸ Шаг 1: планирование структуры (PlanAndSolveAgent)")
        print("-" * 70)
        column_plan = self.planner.plan_column(main_topic)
        print(f"   Заголовок: {column_plan.column_title}")
        print(f"   Подтем: {column_plan.get_topic_count()}")
        print(f"   Аудитория: {column_plan.target_audience}\n")
        
        # Шаг 2: дерево контента для подтем
        mode_name = "ReflectionAgent" if self.use_reflection_mode else "ReActAgent"
        print(f"▸️  Шаг 2: написание статей ({mode_name})")
        print("-" * 70)
        
        content_trees = self._write_topics_sequential(column_plan)
        
        # Шаг 3: сборка колонки
        print("\n▸ Шаг 3: сборка колонки")
        print("-" * 70)
        full_column = self._assemble_column(column_plan, content_trees)
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"▸ Колонка создана! {duration:.1f} сек")
        print(f"{'='*70}\n")
        
#Добавить статистику
        full_column['creation_stats'] = self.stats
        full_column['agent_modes'] = {
            'planner': 'PlanAndSolveAgent',
            'writer': 'ReflectionAgent' if self.use_reflection_mode else 'ReActAgent',
            'reviewer': 'ReviewerAgent' if (self.reviewer and not self.use_reflection_mode) else None,
            'revision': 'RevisionAgent' if (self.revision_agent and not self.use_reflection_mode) else None
        }
        
        return full_column
    
    def _write_topics_sequential(self, column_plan: ColumnPlan) -> List[ContentNode]:
        """Последовательное написание подтем"""
        content_trees = []
        
        for idx, topic in enumerate(column_plan.topics, 1):
            print(f"\n{'─'*70}")
            print(f"▸ Написание {idx}/{column_plan.get_topic_count()}")
            print(f"   Тема: {topic['title']}")
            print(f"{'─'*70}")
            
            tree = self._write_topic_tree(topic, column_plan)
            content_trees.append(tree)
            
# Показать прогресс
            progress = idx / column_plan.get_topic_count() * 100
            print(f"\n▸ Прогресс: {progress:.0f}% ({idx}/{column_plan.get_topic_count()})")
        
        return content_trees
    
    def _write_topic_tree(
        self,
        topic: Dict[str, Any],
        column_context: ColumnPlan
    ) -> ContentNode:
        """Рекурсивное написание дерева подтем"""
        root = ContentNode(
            id=topic['id'],
            title=topic['title'],
            level=ContentLevel.TOPIC,
            description=topic['description']
        )
        
        context = {
            'column_title': column_context.column_title,
            'column_description': column_context.column_description,
            'target_audience': column_context.target_audience,
            'current_topic': topic
        }
        
        self._recursive_write(root, context, level=1)
        return root
    
    def _recursive_write(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        level: int
    ):
        """Рекурсивное написание"""
        if level > self.settings.max_depth:
            indent = "  " * level
            print(f"{indent}▸️  Достигнута макс. глубина {self.settings.max_depth}")
            return
        
        indent = "  " * level
        print(f"\n{indent}{'┈'*40}")
        print(f"{indent}▸ Level {level}: {node.title}")
        print(f"{indent}{'┈'*40}")
        
        if self.use_reflection_mode:
            # Режим 1: ReflectionAgent
            self._write_with_reflection(node, context, level, indent)
        else:
            # Режим 2: ReActAgent
            self._write_with_react(node, context, level, indent)
    
    def _write_with_reflection(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        level: int,
        indent: str
    ):
        """Написание через ReflectionAgent"""
        print(f"{indent}▸️  ReflectionAgent: генерация и оптимизация...")
        
        content_data = self.writer.generate_and_refine_content(node, context, level)
        self.stats['total_generations'] += 1
        
        # ReflectionAgent завершил саморевью
        node.content = content_data['content']
        node.metadata = content_data.get('metadata', {})
        node.metadata['agent_mode'] = 'ReflectionAgent'
        node.metadata['auto_refined'] = True
        
        word_count = content_data.get('word_count', len(content_data['content']))
        print(f"{indent}   Слов: {word_count}")
        print(f"{indent}▸ Контент оптимизирован рефлексией")
        
# Обработка дочерних узлов
        self._process_children(node, content_data, context, level, indent)
    
    def _write_with_react(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        level: int,
        indent: str
    ):
        """Написание через ReActAgent (опциональный ревью)"""
        print(f"{indent}▸️  ReActAgent: генерация...")
        
        content_data = self.writer.generate_content(node, context, level)
        self.stats['total_generations'] += 1
        
        current_content = content_data['content']
        word_count = content_data.get('word_count', len(current_content))
        print(f"{indent}   Слов: {word_count}")
        print(f"{indent}▸ ReActAgent завершил рассуждение и действия")
        
        # Ревью и правки при включённом ревью
        if self.reviewer and self.settings.enable_review:
            current_content, review_metadata = self._review_and_revise(
                node, current_content, content_data, level, indent
            )
            content_data['content'] = current_content
            content_data['metadata'] = {**content_data.get('metadata', {}), **review_metadata}
        
        node.content = current_content
        node.metadata = content_data.get('metadata', {})
        node.metadata['agent_mode'] = 'ReActAgent'
        
# Обработка дочерних узлов
        self._process_children(node, content_data, context, level, indent)
    
    def _review_and_revise(
        self,
        node: ContentNode,
        content: str,
        content_data: Dict[str, Any],
        level: int,
        indent: str
    ) -> tuple:
        """
        Ревью и правка контента при необходимости

        Returns:
            (финальный контент, метаданные ревью)
        """
        target_word_count = get_word_count(level)
        key_points = content_data.get('metadata', {}).get('keywords', [])
        if not key_points:
            key_points = [node.title, node.description]
        
        revision_count = 0
        final_content = content
        review_history = []
        
        while revision_count <= self.settings.max_revisions:
# обзор
            print(f"{indent}▸ Ревью (раунд {revision_count + 1})...")
            review_result = self.reviewer.review_content(
                content=final_content,
                level=level,
                target_word_count=target_word_count,
                key_points=key_points
            )
            self.stats['total_reviews'] += 1
            
            review_history.append({
                'round': revision_count + 1,
                'score': review_result.score,
                'grade': review_result.grade,
                'needs_revision': review_result.needs_revision
            })
            
            print(f"{indent}   Результат: {review_result.score}/100 ({review_result.grade})")
            
            # Проверка прохождения ревью
            if review_result.score >= self.settings.approval_threshold:
                print(f"{indent}▸ Контент прошёл ревью!")
                if revision_count == 0:
                    self.stats['approved_first_try'] += 1
                break
            
            # Проверка лимита правок
            if revision_count >= self.settings.max_revisions:
                print(f"{indent}▸️  Лимит правок ({self.settings.max_revisions}), текущая версия")
                break
            
            # Низкий балл — переписать
            if review_result.score < self.settings.revision_threshold:
                print(f"{indent}▸️  Низкий балл ({review_result.score} < {self.settings.revision_threshold}), переписать")
                self.stats['total_rewrites'] += 1
                # Регенерация
                new_content_data = self.writer.generate_content(
                    node, 
                    {'review_feedback': review_result.reviewer_notes}, 
                    level,
                    additional_requirements=f"Избегайте проблем: {review_result.reviewer_notes}"
                )
                self.stats['total_generations'] += 1
                final_content = new_content_data['content']
            else:
                # Правка
                print(f"{indent}▸ Правка по замечаниям...")
                revised_data = self.revision_agent.revise_content(
                    original_content=final_content,
                    review_result=review_result,
                    target_word_count=target_word_count
                )
                self.stats['total_revisions'] += 1
                final_content = revised_data.get('revised_content', final_content)
            
            revision_count += 1
        
# Создайте метаданные обзора
        final_review = review_history[-1] if review_history else {}
        review_metadata = {
            'review_score': final_review.get('score'),
            'review_grade': final_review.get('grade'),
            'review_rounds': len(review_history),
            'review_history': review_history,
            'reviewed': True
        }
        
        return final_content, review_metadata
    
    def _process_children(
        self,
        node: ContentNode,
        content_data: Dict[str, Any],
        context: Dict[str, Any],
        level: int,
        indent: str
    ):
        """Обработка дочерних узлов"""
        if content_data.get('needs_expansion') and level < self.settings.max_depth:
            subsections = content_data.get('subsections', [])
            if subsections:
                print(f"{indent}▸ Раскрыть {len(subsections)} подузлов")
                
                for subsection in subsections:
                    child = ContentNode(
                        id=subsection['id'],
                        title=subsection['title'],
                        level=ContentLevel(level + 1),
                        description=subsection['description']
                    )
                    node.add_child(child)
                    
                    # Рекурсивно дочерние узлы
                    self._recursive_write(child, context, level + 1)
    
    def _assemble_column(
        self,
        plan: ColumnPlan,
        trees: List[ContentNode]
    ) -> Dict[str, Any]:
        """Сборка полной колонки"""
        articles = []
        
        for tree in trees:
            article_content = self._tree_to_markdown(tree)
            
            articles.append({
                'id': tree.id,
                'title': tree.title,
                'content': article_content,
                'metadata': tree.metadata,
                'word_count': tree.count_words()
            })
        
        return {
            'column_info': {
                'title': plan.column_title,
                'description': plan.column_description,
                'target_audience': plan.target_audience,
                'topic_count': plan.get_topic_count()
            },
            'articles': articles,
            'statistics': self._calculate_statistics(trees)
        }
    
    def _tree_to_markdown(self, node: ContentNode, depth: int = 0) -> str:
        """Дерево контента → markdown"""
        markdown = []
        
        heading_level = "#" * (depth + 1)
        markdown.append(f"{heading_level} {node.title}\n")
        
        if node.content:
            markdown.append(node.content)
            markdown.append("\n")
        
        for child in node.children:
            child_md = self._tree_to_markdown(child, depth + 1)
            markdown.append(child_md)
        
        return "\n".join(markdown)
    
    def _calculate_statistics(self, trees: List[ContentNode]) -> Dict[str, Any]:
        """Вычисление статистики"""
        total_words = 0
        total_nodes = 0
        
        def count_tree(node: ContentNode):
            nonlocal total_words, total_nodes
            total_nodes += 1
            total_words += len(node.content) if node.content else 0
            
            for child in node.children:
                count_tree(child)
        
        for tree in trees:
            count_tree(tree)
        
        return {
            'total_articles': len(trees),
            'total_nodes': total_nodes,
            'total_words': total_words,
            'avg_words_per_article': total_words // len(trees) if trees else 0
        }

