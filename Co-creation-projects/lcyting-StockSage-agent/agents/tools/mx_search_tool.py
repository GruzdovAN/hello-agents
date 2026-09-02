"""
Интеллектуальный помощник по анализу акций — пакет инструментов поиска информации HelloAgents

将东方财富 mx-search Skill 封装为符合 HelloAgents 标准 Tool 接口的工具类。
Агент может использовать этот инструмент для вызова естественного языка для поиска финансовой информации (новостей, исследовательских отчетов, объявлений).
"""

import sys
from pathlib import Path

# Добавьте структуру HelloAgents и путь к навыкам в sys.path
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
_SKILLS_PATH = _PROJECT_ROOT / "skills" / "资讯搜索" / "mx-search"

for p in [_PROJECT_ROOT, _HELLO_PATH, _SKILLS_PATH]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hello_agents.tools import Tool, ToolParameter

from ..text_truncation import truncate_at_natural_boundary

# Верхний предел текстового отображения одного фрагмента информации (символов); Расслабление может уменьшить усечение абстрактного.
MX_SEARCH_CONTENT_MAX_CHARS = 2500


class MXSearchTool(Tool):
"""Инструмент поиска финансовой информации — инкапсуляция восточного чуда богатства mx-search Skill

Поддерживает поиск финансовой информации на естественном языке, в том числе:
- Отдельные акции, связанные с: отчеты об исследованиях, объявления, институциональные мнения
- Отрасль/сектор: новости отрасли, интерпретация политики.
- Макро/рынок: экономический анализ, движение капитала.
- События/правила: объявления о дивидендах, правила торговли и т. д.

Пример использования:
        tool = MXSearchTool(api_key="your_mx_apikey")
result =tool.run({"query": "Последний исследовательский отчет Квейчоу Моутая"})
    """

    def __init__(self, api_key: str = None):
        super().__init__(
            name="mx_search",
            description=(
                "东方财富金融资讯搜索工具。支持搜索A股相关的新闻、研报、公告、"
                "政策解读、行业分析等金融资讯。适用于获取时效性信息和特定事件信息。"
                "支持自然语言查询，如'贵州茅台最新研报'、'人工智能板块近期新闻'、"
«Анализ влияния повышения процентных ставок Федеральной резервной системы на акции А», «Последняя интерпретация новой политики в области энергетических транспортных средств».
            ),
        )

# Получить ключ API: параметры приоритета > переменные среды
        import os
        self.api_key = api_key or os.getenv("MX_APIKEY", "")

# Задержка импорта модуля mx_search
        self._mx_module = None

    def _get_mx_module(self):
"""Отложен импорт модуля mx_search (во избежание ошибок импорта при инициализации)"""
        if self._mx_module is None:
            import mx_search as _mx_search
            self._mx_module = _mx_search
        return self._mx_module

    def get_parameters(self) -> list:
        return [
            ToolParameter(
                name="query",
                type="string",
                description=(
«Оператор запроса на естественном языке. Поддерживает запросы на китайском языке, например:\n»
                    "- 个股资讯: '贵州茅台最新研报', '比亚迪机构观点汇总'\n"
                    "- 行业新闻: '人工智能板块近期新闻', '新能源汽车产业政策'\n"
                    "- 宏观分析: '美联储加息对A股影响分析', '北向资金最新流向'\n"
                    "- 事件公告: '贵州茅台分红派息实施公告', '宁德时代定增预案'\n"
«-Торговые правила: «Ценовой лимит Совета по инновациям в области науки и технологий», «Новые правила подписки на акции»»
                ),
                required=True,
            ),
        ]

    def run(self, parameters: dict) -> str:
        """执行金融资讯搜索

        Args:
параметры: {"query": "Запрос на естественном языке"}

        Returns:
Форматированный текст результатов поиска
        """
        query = parameters.get("query", "")
        if not query:
вернуть «Ошибка: содержимое запроса не может быть пустым»

        if not self.api_key:
            return "错误：MX_APIKEY 未配置，无法搜索资讯。请设置环境变量 MX_APIKEY"

        try:
            mx = self._get_mx_module()

#Создаем экземпляр MXSearch и запрос
            search_client = mx.MXSearch(api_key=self.api_key)
            result = search_client.search(query)

# Форматируем вывод в читаемый текст
            return self._format_result(result, query)

        except Exception as e:
return f"Исключение поиска информации: {str(e)}"

    def _format_result(self, result: dict, query: str) -> str:
"""Форматировать результаты поиска в читаемый текст"""
        lines = []

# Проверьте статус API
        status = result.get("status")
        message = result.get("message", "")
        if status != 0:
lines.append(f"## Результаты поиска информации")
lines.append(f"query: {query}")
            lines.append(f"错误: 状态码 {status} - {message}")
            return "\n".join(lines)

# Анализ результатов поиска
        data = result.get("data", {})
        inner_data = data.get("data", {})
        search_response = inner_data.get("llmSearchResponse", {})
        items = search_response.get("data", [])

        if not items:
return f «Последняя финансовая информация, связанная с «{query}», не найдена»

#Сопоставление типов
        type_map = {
«ОТЧЕТ»: «Отчет об исследовании»,
«НОВОСТИ»: «Новости»,
«ОБЪЯВЛЕНИЕ»: «ОБЪЯВЛЕНИЕ»
        }

# Ограничить количество выводимых элементов
        max_items = 15
        display_items = items[:max_items]

lines.append(f"## Результаты поиска информации")
lines.append(f"query: {query}")
lines.append(f"Всего найдено {len(items)} связанной информации\n")

        for i, item in enumerate(display_items):
title = item.get("title", "Без названия")
            content = item.get("content", "")
            date = item.get("date", "")
            ins_name = item.get("insName", "")
            info_type = item.get("informationType", "")
            rating = item.get("rating", "")
            entity_name = item.get("entityFullName", "")

            type_cn = type_map.get(info_type, info_type or "资讯")

            lines.append(f"### {i+1}. {title}")

            meta_parts = []
            if entity_name:
                meta_parts.append(f"证券: {entity_name}")
            if ins_name:
                meta_parts.append(f"机构: {ins_name}")
            if date:
                meta_parts.append(f"日期: {date.split()[0]}")
lines.append(f"类型: {type_cn} | {' | '.join(meta_parts)}")

            if rating:
lines.append(f"Рейтинг: {rating}")

            if content:
#Обрезать слишком длинный контент (отдавать приоритет абзацам/периодам)
                if len(content) > MX_SEARCH_CONTENT_MAX_CHARS:
                    content = truncate_at_natural_boundary(
                        content, MX_SEARCH_CONTENT_MAX_CHARS, "..."
                    )
                lines.append("")
                lines.append(content)

            lines.append("")

        if len(items) > max_items:
            lines.append(f"*(仅显示前{max_items}条，共{len(items)}条)*")

        return "\n".join(lines)
