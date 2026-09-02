"""
AMiner — китайский академический поисковый инструмент

Получайте китайские научные статьи через AMiner API, чтобы восполнить пробел, к которому CNKI/Wanfang не может получить бесплатный доступ.
AMiner был разработан Университетом Цинхуа и охватывает более 320 миллионов статей и более 130 миллионов ученых.

Адрес регистрации: https://open.aminer.cn/
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import os
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class AminerSearchTool(Tool):
"""AMiner Китайский инструмент академического поиска

Поиск научных статей через AMiner API, особенно хорош для китайских документов и китайских авторов.
Это китайское приложение к Semantic Scholar, охватывающее более 320 миллионов статей.
    """

    SEARCH_URL = "https://datacenter.aminer.cn/gateway/open_platform/api/paper/search"

    def __init__(self):
        super().__init__(
            name="aminer_search",
описание="Получайте научные статьи на китайском и английском языках через AMiner API."
                        "覆盖 3.2 亿+ 论文，擅长中文文献和中文作者搜索。"
                        "当需要检索中文学术论文或中国学者的英文论文时使用此工具。"
                        "需要先注册获取 API Key: https://open.aminer.cn/"
        )

    def _get_api_key(self) -> str:
"""Получить API-ключ AMiner"""
        key = os.getenv("AMINER_API_KEY", "")
        if not key:
            raise RuntimeError(
«Ключ AMiner API не настроен. Пожалуйста, перейдите на https://open.aminer.cn/, чтобы зарегистрироваться и получить его»,
                "然后在 .env 中设置: AMINER_API_KEY=你的key"
            )
        return key

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        max_results = min(parameters.get("max_results", 5), 20)

        if not keyword and not author:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="请至少提供关键词（keyword）或作者（author）"
            )

# AMiner использует параметр title для поиска по ключевым словам
        query = keyword or author
        params = {
            "title": query.strip(),
            "page": "1",
            "size": str(max_results)
        }

        url = f"{self.SEARCH_URL}?{urllib.parse.urlencode(params)}"

        try:
            api_key = self._get_api_key()
            req = urllib.request.Request(url, headers={
                "User-Agent": "PaperAssistant/1.0",
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            })

            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            code = data.get("code", -1)
            if code != 200 and code != 0:
                msg = data.get("msg", data.get("message", "未知错误"))
                return ToolResponse.error(
                    code="API_ERROR",
                    message=f"AMiner API 返回错误 (code={code}): {msg}"
                )

            papers = data.get("data", [])
            if isinstance(papers, dict):
                papers = papers.get("list", papers.get("results", []))

            total = data.get("total", len(papers))

            if not papers:
                return ToolResponse.success(
                    text=f"在 AMiner 中未找到匹配的论文（共 {total} 条结果）。",
                    data={"count": 0, "total": total, "papers": []}
                )

# Форматирование вывода
lines = [f"{len(papers)} статей, найденных в AMiner ({total} результатов):\n"]
            for i, paper in enumerate(papers, 1):
                title = paper.get("title") or paper.get("name") or "N/A"
                paper_id = paper.get("id") or paper.get("paper_id") or ""
                doi = paper.get("doi") or ""
                year = paper.get("year") or paper.get("pub_year") or "N/A"

# автор
                authors_raw = paper.get("authors") or paper.get("author") or []
                if isinstance(authors_raw, list):
                    author_names = []
                    for a in authors_raw:
                        if isinstance(a, dict):
                            author_names.append(a.get("name", ""))
                        elif isinstance(a, str):
                            author_names.append(a)
                    authors_str = ", ".join(author_names[:5])
                    if len(authors_raw) > 5:
                        authors_str += " et al."
                elif isinstance(authors_raw, str):
                    authors_str = authors_raw
                else:
                    authors_str = "N/A"

#Журнал/Конференция
                venue = paper.get("venue") or paper.get("journal") or ""
                if isinstance(venue, dict):
                    venue = venue.get("name", "") or venue.get("raw", "")

# Количество цитирований
                citations = paper.get("n_citation") or paper.get("citation_count") or 0

                lines.append(f"### {i}. {title}")
                if authors_str and authors_str != "N/A":
                    lines.append(f"> 作者: {authors_str}")
                lines.append(f"> 发表: {year} | {venue or 'N/A'}")
                lines.append(f"> 引用: {citations} 次")
                if doi:
                    lines.append(f"> DOI: [{doi}](https://doi.org/{doi})")
                if paper_id:
                    lines.append(f"> AMiner ID: {paper_id}")
                lines.append("")

            return ToolResponse.success(
                text="\n".join(lines),
                data={
                    "count": len(papers),
                    "total": total,
                    "source": "AMiner",
                    "papers": [
                        {
                            "title": p.get("title", ""),
                            "authors": p.get("authors", []),
                            "year": p.get("year", ""),
                            "doi": p.get("doi", ""),
                            "venue": str(p.get("venue", "")),
                        }
                        for p in papers
                    ]
                }
            )

        except urllib.error.HTTPError as e:
            if e.code == 401:
                return ToolResponse.error(
                    code="ACCESS_DENIED",
message="Ключ AMiner API недействителен или срок его действия истек. Проверьте AMINER_API_KEY в .env."
                )
            return ToolResponse.error(
                code="NETWORK_ERROR",
                message=f"AMiner API 请求失败 (HTTP {e.code})"
            )
        except RuntimeError as e:
            return ToolResponse.error(code="ACCESS_DENIED", message=str(e))
        except Exception as e:
            return ToolResponse.error(
                code="INTERNAL_ERROR",
                message=f"AMiner 检索出错: {str(e)}"
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="keyword", type="string",
                         description="搜索关键词，支持中文和英文",
                         required=False),
            ToolParameter(name="author", type="string",
                         description="作者姓名，支持中文名和英文名",
                         required=False),
            ToolParameter(name="max_results", type="integer",
                         description="最大返回结果数（默认5，最大20）",
                         required=False),
        ]
