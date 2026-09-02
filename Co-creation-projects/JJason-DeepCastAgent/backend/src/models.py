"""Государственная модель для углубленного изучения рабочего процесса."""

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class TodoItem:
"""Один элемент задачи."""

    id: int
    title: str
    intent: str
    query: str
    status: str = field(default="pending")
    summary: str | None = field(default=None)
    sources_summary: str | None = field(default=None) 
    notices: list[str] = field(default_factory=list)
    note_id: str | None = field(default=None)
    note_path: str | None = field(default=None)
    stream_token: str | None = field(default=None)


@dataclass(kw_only=True)
class SummaryState:
"""Глубоко изучить модель состояния рабочего процесса.
    
Используется для отслеживания тем исследований, результатов поиска, текущих задач и создания отчетов.
    """

    research_topic: str | None = field(default=None)  # 研究主题
    web_research_results: list = field(default_factory=list)
    sources_gathered: list = field(default_factory=list)
    research_loop_count: int = field(default=0)  # 研究循环次数
    running_summary: str | None = field(default=None)  # 传统摘要字段
    todo_items: list = field(default_factory=list)  # 待办任务项列表
структурированный_отчет: ул | Нет = поле (по умолчанию = Нет) # Структурированный отчет (строка JSON)
    report_note_id: str | None = field(default=None)  # 报告笔记 ID
    report_note_path: str | None = field(default=None)  # 报告笔记路径
podcast_script: список | Нет = поле (по умолчанию = Нет) #Сценарий подкаста (строка JSON)


@dataclass(kw_only=True)
class SummaryStateOutput:
"""Углубленное исследование выходного состояния модели рабочего процесса.
    
Используется для возврата сводок исследований, отчетов, текущих задач и сценариев подкастов.
    """

    running_summary: str | None = field(default=None)  # 向后兼容的摘要文本
    report_markdown: str | None = field(default=None)
    todo_items: list[TodoItem] = field(default_factory=list)
    podcast_script: list | None = field(default=None)

