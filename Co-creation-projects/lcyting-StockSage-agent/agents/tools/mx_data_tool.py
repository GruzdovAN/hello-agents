"""
Интеллектуальный помощник по анализу акций — пакет инструментов для работы с финансовыми данными HelloAgents

将东方财富 mx-data Skill 封装为符合 HelloAgents 标准 Tool 接口的工具类。
Агент может использовать этот инструмент для вызова запросов на естественном языке для получения рыночных, финансовых, взаимоотношений и других данных.
"""

import sys
from pathlib import Path

# Добавьте структуру HelloAgents и путь к навыкам в sys.path
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
_SKILLS_PATH = _PROJECT_ROOT / "skills" / "金融数据" / "mx-data"

for p in [_HELLO_PATH, _SKILLS_PATH]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hello_agents.tools import Tool, ToolParameter


class MXDataTool(Tool):
"""Инструмент запроса финансовых данных - инкапсулирует навык mx-data Oriental Wealth Wonder

Поддерживает запрос финансовых данных, таких как котировки акций A, финансовые показатели, профили компаний, информация об акционерах и т. д., посредством естественного языка.

Пример использования:
        tool = MXDataTool(api_key="your_mx_apikey")
result =tool.run({"query": "Последнее повышение и понижение цен на Квейчоу Мутай"})
    """

    def __init__(self, api_key: str = None):
        super().__init__(
            name="mx_data",
            description=(
«Инструмент запроса финансовых данных Oriental Fortune. Поддерживает запрос котировок акций категории А в реальном времени и за прошлые периоды».
                "财务指标（净利润、ROE、毛利率等）、公司概况（主营业务、高管信息）、"
«Информация об акционерах (десять крупнейших акционеров), котировки индексов, котировки секторов и т. д.»
«Поддержка запросов на естественном языке, таких как «Чистая операционная прибыль Kweichow Moutai за последние три года»,»
«Последние показатели индекса CSI 300», «Профиль компании BYD и основной бизнес».
            ),
        )

# Получить ключ API: параметры приоритета > переменные среды
        import os
        self.api_key = api_key or os.getenv("MX_APIKEY", "")

# Задержка импорта модуля mx_data
        self._mx_module = None

    def _get_mx_module(self):
"""Отложен импорт модуля mx_data (во избежание ошибок импорта при инициализации)"""
        if self._mx_module is None:
            import mx_data as _mx_data
            self._mx_module = _mx_data
        return self._mx_module

    def get_parameters(self) -> list:
        return [
            ToolParameter(
                name="query",
                type="string",
                description=(
«Оператор запроса на естественном языке. Поддерживает запросы на китайском языке, например:\n»
                    "- 行情: '贵州茅台最新价 涨跌幅', '比亚迪近一年每个交易日收盘价'\n"
                    "- 财务: '贵州茅台近三年净利润 营业收入 净资产收益率'\n"
«-Компания: «Профиль компании BYD, основной вид деятельности, кто является председателем»\n»
«-Акционеры: «Десять крупнейших акционеров Kweichow Moutai»\n»
«-Индекс: «Последняя точка индекса CSI 300»»
                ),
                required=True,
            ),
        ]

    def run(self, parameters: dict) -> str:
"""Выполнить запрос финансовых данных

        Args:
параметры: {"query": "Запрос на естественном языке"}

        Returns:
Форматированный текст результата запроса
        """
        query = parameters.get("query", "")
        if not query:
вернуть «Ошибка: содержимое запроса не может быть пустым»

        if not self.api_key:
            return "错误：MX_APIKEY 未配置，无法查询金融数据。请设置环境变量 MX_APIKEY"

        try:
            mx = self._get_mx_module()

#Создаем экземпляр MXData и запрос
            data_querier = mx.MXData(api_key=self.api_key)
            result = data_querier.query(query)

# Результаты анализа
            tables, condition_parts, total_rows, error = mx.MXData.parse_result(result)

            if error:
return f"Ошибка запроса: {error}"

            if not tables:
return «Запрос не вернул никаких данных»

# Форматирование вывода
            return self._format_result(tables, condition_parts, total_rows)

        except Exception as e:
return f"Исключение в запросе финансовых данных: {str(e)}"

    def _format_result(self, tables: list, condition_parts: list, total_rows: int) -> str:
"""Форматировать результаты запроса в читаемый текст"""
        lines = []

# Условия запроса
        if condition_parts:
lines.append("## Условия запроса")
            for part in condition_parts:
                lines.append(part)
            lines.append("")

# Таблица данных
        lines.append(f"## 查询结果（{len(tables)}个表，共{total_rows}行数据）\n")

        for idx, table in enumerate(tables):
            sheet_name = table.get("sheet_name", f"表{idx+1}")
            rows = table.get("rows", [])
            fieldnames = table.get("fieldnames", [])

            lines.append(f"### {sheet_name}")

            if not rows:
lines.append("(Нет данных)")
                continue

# Ограничьте количество строк вывода (чтобы избежать слишком длинного контекста)
            max_rows = 30
            display_rows = rows[:max_rows]

# Заголовок
            header = " | ".join(fieldnames[:10])  # 最多显示10列
            lines.append(f"| {header} |")
            lines.append(f"|{'|'.join(['---'] * min(len(fieldnames), 10))}|")

# строка данных
            for row in display_rows:
                values = [str(row.get(col, "")) for col in fieldnames[:10]]
                lines.append(f"| {' | '.join(values)} |")

            if len(rows) > max_rows:
                lines.append(f"\n*(仅显示前{max_rows}行，共{len(rows)}行)*")

            lines.append("")

        return "\n".join(lines)
