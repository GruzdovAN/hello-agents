"""
Инструмент поиска биомедицинской литературы PubMed

通过 NCBI Entrez API (E-utilities) 检索 PubMed 数据库中的生物医学论文。
Это самая авторитетная база данных в области биомедицины, охватывающая более 36 миллионов статей.

API 文档: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""
import urllib.request
import urllib.parse
import urllib.error
import ssl
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus

# Совместимость с Windows SSL
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


class PubMedSearchTool(Tool):
"""Инструмент для поиска биомедицинской литературы PubMed

Поиск в базе данных PubMed/PMC через API NCBI Entrez.
Охватывает все области биомедицины, такие как медицина, биология, фармация, сестринское дело и общественное здравоохранение.
    """

    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self):
        super().__init__(
            name="pubmed_search",
            description="在 PubMed 数据库中检索生物医学论文。"
                        "覆盖 3600 万+ 论文，涵盖医学、生物学、药学、护理学、"
«Общественное здравоохранение и все области биомедицины».
                        "支持 MeSH 主题词搜索、作者、期刊、年份等筛选。"
«Подходит для медицинских исследований, разработки лекарств, клинической практики и других сценариев».
        )

    def _search_pmids(self, query: str, max_results: int = 5,
                       year_from: str = "", year_to: str = "") -> List[str]:
"""Поиск возвращает список PMID"""
# Создаем условия запроса
        search_terms = [query.strip()]
        if year_from or year_to:
            from_year = year_from or "1900"
            to_year = year_to or "2026"
            search_terms.append(f"{from_year}:{to_year}[dp]")

        full_query = " AND ".join(search_terms)

        params = {
            "db": "pubmed",
            "term": full_query,
            "retmax": str(max_results),
            "retmode": "xml",
            "sort": "relevance"
        }

        url = f"{self.SEARCH_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "PaperAssistant/1.0"})

        with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx) as resp:
            root = ET.fromstring(resp.read().decode("utf-8"))
            id_list = root.find(".//IdList")
            if id_list is None:
                return []
            return [elem.text for elem in id_list.findall("Id")]

    def _fetch_summaries(self, pmids: List[str]) -> List[Dict[str, Any]]:
"""Получить реферативную информацию"""
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }

        url = f"{self.SUMMARY_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "PaperAssistant/1.0"})

        with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx) as resp:
            root = ET.fromstring(resp.read().decode("utf-8"))

        papers = []
        for doc in root.findall(".//DocSum"):
            paper = {
                "pmid": doc.find("Id").text if doc.find("Id") is not None else "",
                "title": "N/A",
                "authors": [],
                "pubdate": "N/A",
                "source": "N/A",
                "doi": "",
            }

            for item in doc.findall("Item"):
                name = item.get("Name", "")
                if name == "Title":
                    paper["title"] = item.text or "N/A"
                elif name == "AuthorList":
                    paper["authors"] = [a.text for a in item.findall("Item")
                                       if a.text]
                elif name == "PubDate":
                    paper["pubdate"] = item.text or "N/A"
                elif name == "Source":
                    paper["source"] = item.text or "N/A"
                elif name == "DOI":
                    paper["doi"] = item.text or ""

            papers.append(paper)

        return papers

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        max_results = min(parameters.get("max_results", 5), 20)
        year_from = parameters.get("year_from", "")
        year_to = parameters.get("year_to", "")

        if not keyword and not author:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="请至少提供关键词（keyword）或作者（author）"
            )

# Построить запрос
        query_parts = []
        if keyword:
            query_parts.append(keyword.strip())
        if author:
            query_parts.append(f'{author.strip()}[Author]')
        query = " AND ".join(query_parts)

        try:
            pmids = self._search_pmids(query, max_results, year_from, year_to)

            if not pmids:
                return ToolResponse.success(
                    text=f"在 PubMed 中未找到匹配的论文。\n"
                         f"建议：尝试更简短的关键词、使用 MeSH 主题词、"
f" или проверьте правописание. Запрос: {query}",
                    data={"count": 0, "papers": []}
                )

            papers = self._fetch_summaries(pmids)

# Форматирование вывода
            lines = [f"在 PubMed 中找到 {len(papers)} 篇论文：\n"]
            for i, p in enumerate(papers, 1):
                authors_str = ", ".join(p["authors"][:3])
                if len(p["authors"]) > 3:
                    authors_str += " et al."
                lines.append(f"### {i}. {p['title']}")
                if authors_str:
                    lines.append(f"> 作者: {authors_str}")
lines.append(f"> PMID: {p['pmid']} | Опубликовано: {p['pubdate']} | {p['source']}")
                if p.get("doi"):
                    lines.append(f"> [DOI](https://doi.org/{p['doi']}) | "
                                f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/)")
                lines.append("")

            lines.append(f"---")
            lines.append(f"*数据来源: PubMed/NCBI*")

            return ToolResponse.success(
                text="\n".join(lines),
                data={"count": len(papers), "papers": papers, "query": query}
            )

        except urllib.error.HTTPError as e:
            return ToolResponse.error(
                code="NETWORK_ERROR",
                message=f"PubMed API 请求失败 (HTTP {e.code})"
            )
        except Exception as e:
            return ToolResponse.error(
                code="INTERNAL_ERROR",
                message=f"PubMed 检索出错: {str(e)}"
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="keyword", type="string",
описание="Поиск ключевых слов, поддержка ключевых слов MeSH, таких как "метформин для лечения диабета"",
                         required=False),
            ToolParameter(name="author", type="string",
                         description="作者姓名，如 'Anthony Fauci'",
                         required=False),
            ToolParameter(name="year_from", type="string",
                         description="起始年份", required=False),
            ToolParameter(name="year_to", type="string",
                         description="截止年份", required=False),
            ToolParameter(name="max_results", type="integer",
описание="Максимальное количество возвращаемых результатов (по умолчанию 5, максимум 20)", требуется=False),
        ]
