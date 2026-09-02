"""
Инструмент поиска API arXiv

Ищите научные статьи через официальный API arXiv и получайте структурированные результаты.
Документация: https://info.arxiv.org/help/api/.
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class ArxivSearchTool(Tool):
"""инструмент поиска академических статей arXiv

Извлекайте научные статьи из базы данных arXiv, поддерживая поиск по ключевым словам, фильтрацию авторов, временной диапазон и другие условия.
Возвращает название статьи, автора, аннотацию, дату публикации и ссылку PDF.
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        super().__init__(
            name="arxiv_search",
описание="Поиск статей в базе данных научных статей arXiv."
«Поддерживает фильтрацию по ключевым словам, авторам и временному диапазону».
«Возвращает название статьи, автора, аннотацию, дату публикации и ссылку».
«Используйте этот инструмент, когда вам нужно найти последние научные исследования».
        )

    def _build_query(self, parameters: Dict[str, Any]) -> str:
"""Построение строки запроса API arXiv"""
        parts = []
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        category = parameters.get("category", "")

        if keyword:
# URL-адрес кодирует ключевые слова и строит запрос
            terms = [f"all:{t.strip()}" for t in keyword.split() if t.strip()]
            parts.append("+AND+".join(terms))

        if author:
            parts.append(f'au:{author.replace(" ", "+")}')

        if category:
# Классификация arXiv, такая как cs.AI, cs.CL, stat.ML
            parts.append(f"cat:{category.strip()}")

        if not parts:
            parts.append("all:machine+learning")  # 默认查询

        return "+AND+".join(parts)

    def _parse_atom_response(self, xml_text: str) -> List[Dict[str, Any]]:
"""Разбор XML-кода Atom, возвращенного API arXiv"""
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }

        root = ET.fromstring(xml_text)
        entries = root.findall("atom:entry", ns)

        papers = []
        for entry in entries:
            title = entry.find("atom:title", ns)
            authors = entry.findall("atom:author", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            link = None
            for l in entry.findall("atom:link", ns):
                if l.get("title") == "pdf" or l.get("type") == "application/pdf":
                    link = l.get("href")
                    break
            if not link:
# Используйте id для создания ссылки на страницу arXiv
                paper_id = entry.find("atom:id", ns)
                if paper_id is not None and paper_id.text:
                    arxiv_id = paper_id.text.split("/abs/")[-1]
                    link = f"https://arxiv.org/pdf/{arxiv_id}"

            paper = {
                "title": title.text.strip().replace("\n", " ") if title is not None and title.text else "N/A",
                "authors": [a.find("atom:name", ns).text
                           for a in authors if a.find("atom:name", ns) is not None],
                "summary": summary.text.strip().replace("\n", " ")[:500]
                          if summary is not None and summary.text else "N/A",
                "published": published.text[:10] if published is not None and published.text else "N/A",
                "pdf_url": link or "N/A"
            }
            papers.append(paper)

        return papers

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        max_results = min(parameters.get("max_results", 5), 20)

        if not keyword and not author:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="请至少提供关键词（keyword）或作者（author）"
            )

        query = self._build_query(parameters)
        url = f"{self.BASE_URL}?search_query={query}&max_results={max_results}&sortBy=relevance"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PaperAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read().decode("utf-8")

            papers = self._parse_atom_response(xml_data)

            if not papers:
                return ToolResponse.success(
text="Подходящая статья не найдена, попробуйте изменить ключевые слова.",
                    data={"count": 0, "papers": []}
                )

# Форматирование вывода
            lines = [f"找到 {len(papers)} 篇论文：\n"]
            for i, p in enumerate(papers, 1):
                authors_str = ", ".join(p["authors"][:3])
                if len(p["authors"]) > 3:
                    authors_str += " et al."
                lines.append(f"### {i}. {p['title']}")
                lines.append(f"   作者: {authors_str}")
                lines.append(f"   发表: {p['published']}")
                lines.append(f"   摘要: {p['summary'][:300]}...")
                lines.append(f"   PDF: {p['pdf_url']}")
                lines.append("")

            return ToolResponse.success(
                text="\n".join(lines),
                data={"count": len(papers), "papers": papers, "query": query}
            )

        except urllib.error.URLError as e:
            return ToolResponse.error(
                code="NETWORK_ERROR",
message=f"Ошибка запроса API arXiv: {str(e)}"
            )
        except ET.ParseError as e:
            return ToolResponse.error(
                code="INVALID_FORMAT",
                message=f"解析 arXiv 返回数据失败: {str(e)}"
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
описание="Поиск по ключевым словам, например, "рассуждение на основе большой языковой модели"",
                required=False
            ),
            ToolParameter(
                name="author", type="string",
                description="作者姓名，如 'Geoffrey Hinton'",
                required=False
            ),
            ToolParameter(
                name="category", type="string",
description="Классификация arXiv, например cs.AI (искусственный интеллект) / cs.CL (компьютерная лингвистика) / stat.ML (машинное обучение)",
                required=False
            ),
            ToolParameter(
                name="max_results", type="integer",
описание="Максимальное количество возвращаемых результатов (по умолчанию 5, максимум 20)",
                required=False
            ),
        ]
