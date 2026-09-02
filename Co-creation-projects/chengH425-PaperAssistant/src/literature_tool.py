"""
Инструмент поиска литературы — API Semantic Scholar

Охватывает более 200 миллионов научных статей по информатике, медицине, биологии, физике, химии,
Все предметные области, включая социальные науки, экономику, гуманитарные науки и искусство.

API 文档: https://api.semanticscholar.org/api-docs/
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import os
import time
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class LiteratureSearchTool(Tool):
"""Полнопрофильный инструмент поиска литературы

Ищите научные статьи в междисциплинарных базах данных с помощью Semantic Scholar API.
Охватывает более 200 миллионов статей и поддерживает условия фильтрации, такие как ключевые слова, авторы, годы, предметные области и т. д.
Возвращает название статьи, автора, аннотацию, информацию о публикации, количество цитирований, ссылку PDF и т. д.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

#Запрашиваемые бумажные поля
    FIELDS = [
        "title", "abstract", "authors", "year", "venue",
        "externalIds", "citationCount", "influentialCitationCount",
        "openAccessPdf", "journal", "publicationTypes", "fieldsOfStudy"
    ]

# Сопоставление ключевых слов по теме китайского языка
    FIELD_ALIASES = {
«Информатика»: «Информатика»,
«Искусственный интеллект»: «Искусственный интеллект»,
«Машинное обучение»: «Машинное обучение»,
«Медицина»: «Медицина»,
«Биология»: «Биология»,
«Физика»: «Физика»,
«Химия»: «Химия»,
«Математика»: «Математика»,
«Экономика»: «Экономика»,
«Психология»: «Психология»,
«Социология»: «Социология»,
«Лингвистика»: «Лингвистика»,
«Философия»: «Философия»,
«История»: «История»,
«Инжиниринг»: «Инжиниринг»,
«Наука об окружающей среде»: «Наука об окружающей среде»,
«Материаловедение»: «Материаловедение»,
«Образование»: «Образование»,
«Закон»: «Закон»,
«Политология»: «Политология»,
«Коммерция»: «Бизнес»,
«Искусство»: «Искусство»,
«География»: «География»,
«Геология»: «Геология»,
    }

    def __init__(self):
        super().__init__(
            name="literature_search",
            description="通过 Semantic Scholar 在全学科数据库中检索学术论文。"
                        "覆盖 2 亿+ 论文，涵盖计算机科学、医学、生物、物理、化学、"
«Социальные науки, экономика, гуманитарные науки, все академические области».
                        "支持按关键词、作者、年份范围、学科领域筛选。"
                        "返回论文标题、作者、摘要、期刊、引用次数、PDF 链接等信息。"
                        "当需要跨学科检索学术文献时使用此工具，比 arXiv 覆盖面更广。"
        )

    def _map_field(self, field_input: str) -> str:
"""Сопоставление китайских/нечетких названий предметов с полями Semantic Scholar"""
        if not field_input:
            return ""
        field_input = field_input.strip()
# Прямое совпадение
        for cn, en in self.FIELD_ALIASES.items():
            if cn in field_input or field_input.lower() in cn.lower():
                return en
# Если он уже на английском языке, вернитесь напрямую
        return field_input

    def _build_url(self, parameters: Dict[str, Any]) -> str:
"""Создание URL-адреса поиска Semantic Scholar"""
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        field = parameters.get("field", "")
        year_from = parameters.get("year_from", "")
        year_to = parameters.get("year_to", "")
        limit = min(parameters.get("max_results", 5), 20)

# Создаем строку запроса
        query_parts = []
        if keyword:
            query_parts.append(keyword.strip())
        if author:
            query_parts.append(f'author:"{author.strip()}"')

        query = " ".join(query_parts) if query_parts else "machine learning"

        params = {
            "query": query,
            "limit": str(limit),
            "fields": ",".join(self.FIELDS)
        }

# Тематический фильтр
        mapped_field = self._map_field(field) if field else ""
        if mapped_field:
            params["fieldsOfStudy"] = mapped_field

# Фильтр года
        if year_from or year_to:
            year_filter = f"{year_from or '1900'}-{year_to or '2026'}"
            params["year"] = year_filter

        return f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

    def _format_paper(self, paper: Dict, index: int, keyword: str = "") -> str:
"""Отформатируйте отдельный документ как Markdown"""
        title = paper.get("title", "N/A")
        year = paper.get("year", "N/A")
        venue = paper.get("venue", "")
        journal = paper.get("journal", {})
        journal_name = journal.get("name", "") if journal else ""
        publication_venue = venue or journal_name or "N/A"

# Список авторов
        authors_list = paper.get("authors", [])
        author_names = [a.get("name", "") for a in authors_list[:5]]
        authors_str = ", ".join(author_names)
        if len(authors_list) > 5:
            authors_str += " et al."

# Аннотация: сначала возьмите TLDR, затем абстрагируйте
Abstract = paper.get("абстракт") или "Пока нет реферата"
        if len(abstract) > 400:
            abstract = abstract[:400] + "..."

# Количество цитирований
        citations = paper.get("citationCount", 0)

        # DOI
        external_ids = paper.get("externalIds", {}) or {}
        doi = external_ids.get("DOI", "")

# PDF-ссылка
        open_access = paper.get("openAccessPdf", {}) or {}
        pdf_url = open_access.get("url", "")
        arxiv_id = external_ids.get("ArXiv", "")

# тег поля
        fields = paper.get("fieldsOfStudy", []) or []
        fields_str = ", ".join(fields[:3]) if fields else ""

        lines = [f"### {index}. {title}"]
        if authors_str:
            lines.append(f"> 作者: {authors_str}")
        lines.append(f"> 发表: {year} | {publication_venue}")
        if fields_str:
lines.append(f"> поля: {fields_str}")
lines.append(f"> citations: {citations} next")

# Связь
        links = []
        if doi:
            links.append(f"[DOI](https://doi.org/{doi})")
        if pdf_url:
            links.append(f"[PDF]({pdf_url})")
        if arxiv_id:
            links.append(f"[arXiv](https://arxiv.org/abs/{arxiv_id})")
        if links:
            lines.append(f"> {' | '.join(links)}")

        lines.append(f">> {abstract}")
        lines.append("")
        return "\n".join(lines)

    def _make_request(self, url: str, api_key: str, max_retries: int = 3) -> Dict:
"""Отправить запрос API, повторить попытку с экспоненциальной задержкой"""
        last_error = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "PaperAssistant/1.0",
                        "Accept": "application/json"
                    }
                )
                if api_key:
                    req.add_header("x-api-key", api_key)

                with urllib.request.urlopen(req, timeout=20) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            except urllib.error.HTTPError as e:
                if e.code == 429:
# Ограничение скорости: подождите и попробуйте еще раз
                    wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    if attempt < max_retries - 1:
                        time.sleep(wait)
                        continue
                    raise RuntimeError(
                        "API 请求频率已达上限（429 Too Many Requests）。\n"
                        "Semantic Scholar 免费额度为 100 次/5 分钟。\n"
                        "请稍等 1-5 分钟后重试，或申请免费 API Key：\n"
                        "https://www.semanticscholar.org/product/api\n"
                        "获取后在 .env 中设置 SEMANTIC_SCHOLAR_API_KEY"
                    ) from e
                raise RuntimeError(
                    f"Semantic Scholar API 返回 HTTP {e.code}: {e.reason}"
                ) from e
            except urllib.error.URLError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise RuntimeError(f"网络连接失败: {str(e.reason)}") from e

        raise RuntimeError(f"请求失败（已重试 {max_retries} 次）: {last_error}")

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        field = parameters.get("field", "")

        if not keyword and not author:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="请至少提供关键词（keyword）或作者（author）"
            )

        url = self._build_url(parameters)
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

        try:
            data = self._make_request(url, api_key)

            papers = data.get("data", [])
            total = data.get("total", 0)
            offset = data.get("offset", 0)

            if not papers:
# Попробуйте порекомендовать похожие поисковые запросы
                suggestion = ""
                if keyword:
предложение = f"\n\nПредложение: попробуйте более короткие ключевые слова или измените синонимы. Например, замените '{keyword}' на более общее выражение."
                return ToolResponse.success(
                    text=f"未找到匹配的论文（共 {total} 条结果）。{suggestion}",
                    data={"count": 0, "total": total, "papers": []}
                )

# Форматирование вывода
lines = [f"{total} найденных документов (показаны первые {len(papers)}, смещение {offset}):\n"]
            for i, paper in enumerate(papers, 1):
                lines.append(self._format_paper(paper, i, keyword))

            lines.append(f"---")
            lines.append(f"*本次检索共 {total} 篇结果。如需更多，请调整关键词或筛选条件。*")
            if total > len(papers):
                lines.append(f"*提示：可通过增加 max_results 获取更多结果（最大 20）。*")

            return ToolResponse.success(
                text="\n".join(lines),
                data={
                    "count": len(papers),
                    "total": total,
                    "offset": offset,
                    "papers": [
                        {
                            "title": p.get("title"),
                            "authors": [a.get("name") for a in p.get("authors", [])],
                            "year": p.get("year"),
                            "venue": p.get("venue", ""),
                            "citationCount": p.get("citationCount", 0),
                            "abstract": (p.get("abstract") or "")[:300],
                            "doi": (p.get("externalIds") or {}).get("DOI", ""),
                            "fieldsOfStudy": p.get("fieldsOfStudy", [])
                        }
                        for p in papers
                    ]
                }
            )

        except RuntimeError as e:
# _make_request уже содержит логику повтора, вот окончательный сбой
            return ToolResponse.error(
                code="API_ERROR",
message=f"[Ошибка получения] {str(e)}\n\n"
«Пожалуйста, подождите 1–2 минуты и повторите попытку. Тем временем можно использовать другие источники данных (OpenAlex, CrossRef, PubMed).»
            )
        except json.JSONDecodeError:
            return ToolResponse.error(
                code="INVALID_FORMAT",
                message="解析 API 返回数据失败，请稍后重试。"
            )
        except Exception as e:
            return ToolResponse.error(
                code="INTERNAL_ERROR",
message=f"Ошибка при получении: {str(e)}"
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="keyword", type="string",
описание="Поиск по ключевым словам, поддержка китайского и английского языков. Например, "механизм преобразования внимания" или "сегментация изображений глубокого обучения"",
                required=False
            ),
            ToolParameter(
                name="author", type="string",
                description="作者姓名，如 'Geoffrey Hinton' 或 '何恺明'",
                required=False
            ),
            ToolParameter(
                name="field", type="string",
описание="Предметная область, поддерживает китайский и английский языки. Например, "Информатика"/"Информатика", "Медицина"/"Медицина", "Физика"/"Физика"",
                required=False
            ),
            ToolParameter(
                name="year_from", type="string",
описание="Начальный год, например '2020'",
                required=False
            ),
            ToolParameter(
                name="year_to", type="string",
описание="Год окончания, например '2026'",
                required=False
            ),
            ToolParameter(
                name="max_results", type="integer",
описание="Максимальное количество возвращаемых результатов (по умолчанию 5, максимум 20)",
                required=False
            ),
        ]
