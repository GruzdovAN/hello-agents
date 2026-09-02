"""
Инструмент поиска журнальных статей Crossref

Поиск опубликованных статей в научных журналах с помощью Crossref REST API.
Crossref — это реестр DOI научных публикаций, охватывающий более 150 миллионов записей.

Документация API: https://api.crossref.org/.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class CrossRefSearchTool(Tool):
"""Инструмент поиска журнальных статей CrossRef

Ищите официально опубликованные журнальные статьи, статьи на конференциях, книги и т. д. с помощью Crossref REST API.
Охватывает более 150 миллионов научных работ и содержит наиболее полные метаданные журнальных статей (DOI, ISSN, номера страниц и т. д.).
Особенно подходит для поиска официально опубликованных журнальных статей и получения метаданных цитирования.
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self):
        super().__init__(
            name="crossref_search",
            description="通过 CrossRef API 检索正式发表的期刊论文和会议论文。"
                        "覆盖 1.5 亿+ 记录，拥有最完整的引用元数据（DOI、期刊名、"
                        "卷号、页码等）。特别适合按 DOI 查找论文或检索特定期刊的文献。"
«Используйте этот инструмент, когда требуется точная информация о цитировании».
        )

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        doi = parameters.get("doi", "")
        journal = parameters.get("journal", "")
        max_results = min(parameters.get("max_results", 5), 20)
        year_from = parameters.get("year_from", "")
        year_to = parameters.get("year_to", "")

# Точный запрос DOI (самый эффективный)
        if doi:
            url = f"{self.BASE_URL}/{urllib.parse.quote(doi.strip(), safe='')}"
        else:
            if not keyword and not author and not journal:
                return ToolResponse.error(
                    code="INVALID_PARAM",
message="Пожалуйста, укажите ключевое слово (keyword), автора (author), DOI (doi) или название журнала (journal)"
                )

# Создаем условия фильтра
            filters = []
            if year_from or year_to:
                f = f"from-pub-date:{year_from or '1900'}"
                if year_to:
                    f += f",until-pub-date:{year_to}"
                filters.append(f)

# Поле запроса
            query_parts = []
            if keyword:
                query_parts.append(keyword.strip())
            if author:
                query_parts.append(author.strip())
            if journal:
                query_parts.append(journal.strip())

            params = {
                "query": " ".join(query_parts),
                "rows": str(max_results),
            }
            if filters:
                params["filter"] = ",".join(filters)

            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "PaperAssistant/1.0 (mailto:1793636425@qq.com)",
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

# Результаты анализа
            if doi:
#Один бумажный запрос
                msg = data.get("message", {})
                items = [msg] if msg else []
                total = len(items)
            else:
                msg = data.get("message", {})
                items = msg.get("items", [])
                total = msg.get("total-results", 0)

            if not items:
                return ToolResponse.success(
                    text=f"在 CrossRef 中未找到匹配的论文。"
                         f"{' DOI 可能不正确。' if doi else ' 请尝试更换关键词。'}",
                    data={"count": 0, "papers": []}
                )

# Форматирование вывода
            lines = [f"找到 {total} 篇论文（显示前 {len(items)} 篇）：\n"]
            for i, item in enumerate(items, 1):
                title_list = item.get("title", ["N/A"])
                title = title_list[0] if title_list else "N/A"

# автор
                authors = item.get("author", [])
                author_names = []
                for a in authors[:5]:
                    given = a.get("given", "")
                    family = a.get("family", "")
                    if given or family:
                        author_names.append(f"{family} {given}".strip())
                authors_str = ", ".join(author_names)
                if len(authors) > 5:
                    authors_str += " et al."

# Опубликовать сообщение
                published = item.get("published-print", {}) or item.get("published-online", {})
                pub_date = "-".join(str(v) for v in published.get("date-parts", [["?"]])[0]) if published else "N/A"

#журнал
                container = item.get("container-title", [])
                venue = container[0] if container else item.get("publisher", "N/A")

# Количество цитирований
                ref_count = item.get("is-referenced-by-count", 0)

                item_doi = item.get("DOI", "")

                lines.append(f"### {i}. {title}")
                if authors_str:
                    lines.append(f"> 作者: {authors_str}")
                lines.append(f"> 发表: {pub_date} | {venue}")
                lines.append(f"> 引用: {ref_count} 次")
                if item_doi:
                    lines.append(f"> DOI: [{item_doi}](https://doi.org/{item_doi})")
                lines.append("")

            lines.append(f"---")
lines.append(f"*Источник данных: Crossref API*")

            return ToolResponse.success(
                text="\n".join(lines),
                data={"count": len(items), "total": total, "papers": items}
            )

        except urllib.error.HTTPError as e:
            return ToolResponse.error(
                code="NETWORK_ERROR",
                message=f"CrossRef API 请求失败 (HTTP {e.code})"
            )
        except json.JSONDecodeError:
            return ToolResponse.error(
                code="INVALID_FORMAT",
message="Не удалось проанализировать данные, возвращенные Crossref"
            )
        except Exception as e:
            return ToolResponse.error(
                code="INTERNAL_ERROR",
message=f"Ошибка получения CrossRef: {str(e)}"
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="keyword", type="string",
                         description="搜索关键词", required=False),
            ToolParameter(name="author", type="string",
                         description="作者姓名", required=False),
            ToolParameter(name="doi", type="string",
описание="Номер DOI (точный запрос, высший приоритет)", требуется=False),
            ToolParameter(name="journal", type="string",
                         description="期刊名称", required=False),
            ToolParameter(name="year_from", type="string",
                         description="起始年份", required=False),
            ToolParameter(name="year_to", type="string",
                         description="截止年份", required=False),
            ToolParameter(name="max_results", type="integer",
описание="Максимальное количество возвращаемых результатов (по умолчанию 5, максимум 20)", требуется=False),
        ]
