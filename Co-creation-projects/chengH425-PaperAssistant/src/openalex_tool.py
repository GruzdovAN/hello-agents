"""
OpenAlex открытый инструмент поиска академических ресурсов

OpenAlex — полностью открытый и бесплатный каталог академической литературы.
聚合了 CrossRef、PubMed、arXiv、DOAJ 等多个来源，覆盖 2.5 亿+ 学术作品。

Документация по API: https://docs.openalex.org/.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class OpenAlexSearchTool(Tool):
"""Открытый инструмент поиска академических ресурсов OpenAlex

Ищите глобальную научную литературу с помощью OpenAlex REST API.
Объединить несколько источников данных (CrossRef, PubMed, arXiv, DOAJ, ORCID и т. д.),
Охватывает более 250 миллионов работ, более 90 миллионов авторов и более 100 000 журналов/конференций.
Полностью бесплатно, не требуется ключ API, открытые данные (протокол CC0).
    """

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self):
        super().__init__(
            name="openalex_search",
описание="Поиск мировой научной литературы через API OpenAlex."
                        "覆盖 2.5 亿+ 作品，聚合多个数据源，完全免费无需 Key。"
                        "支持按关键词、作者、机构、期刊、年份、开放获取状态等筛选。"
                        "特别适合检索开放获取（OA）论文和跨数据库的综合检索。"
        )

    def _format_authorship(self, authorships: List[Dict]) -> str:
        """格式化作者列表"""
        names = []
        for a in authorships[:5]:
            author = a.get("author", {})
            name = author.get("display_name", "")
            if name:
                names.append(name)
        result = ", ".join(names)
        if len(authorships) > 5:
            result += " et al."
        return result or "N/A"

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        keyword = parameters.get("keyword", "")
        author = parameters.get("author", "")
        institution = parameters.get("institution", "")
        max_results = min(parameters.get("max_results", 5), 20)
        year_from = parameters.get("year_from", "")
        year_to = parameters.get("year_to", "")
        open_access_only = parameters.get("open_access_only", False)

        if not keyword and not author and not institution:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="请至少提供关键词(keyword)、作者(author)或机构(institution)"
            )

# Создание параметров поиска
        params: Dict[str, Any] = {
            "per-page": str(max_results),
            "sort": "cited_by_count:desc",
        }

# Ключевые слова для поиска
        search_terms = []
        if keyword:
            search_terms.append(keyword.strip())
        if author:
            search_terms.append(f"author.display_name.search:{author.strip()}")
        if institution:
            search_terms.append(f"authorships.institutions.display_name.search:{institution.strip()}")

        if search_terms:
            params["search"] = " ".join(search_terms)

# Фильтр года
        if year_from:
            params["filter"] = params.get("filter", "") + f"from_publication_date:{year_from}-01-01,"
        if year_to:
            params["filter"] = params.get("filter", "") + f"to_publication_date:{year_to}-12-31,"

# фильтрация открытого доступа
        if open_access_only:
            params["filter"] = params.get("filter", "") + "is_oa:true,"

# Очистка конечных запятых
        if "filter" in params:
            params["filter"] = params["filter"].rstrip(",")
            if not params["filter"]:
                del params["filter"]

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "PaperAssistant/1.0",
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = data.get("results", [])
            meta = data.get("meta", {})
            total = meta.get("count", 0)

            if not results:
                return ToolResponse.success(
                    text=f"在 OpenAlex 中未找到匹配的论文（共 {total} 条结果）。",
                    data={"count": 0, "total": total, "papers": []}
                )

# Форматирование вывода
lines = [f"{total} найдено статей (показаны первые {len(results)} статей, отсортированные по количеству цитирований):\n"]
            for i, work in enumerate(results, 1):
                title = work.get("display_name", work.get("title", "N/A"))

                authors_str = self._format_authorship(work.get("authorships", []))

                pub_date = work.get("publication_date", "N/A")

#Название журнала/конференции
                source = work.get("primary_location", {}) or {}
                source_obj = source.get("source", {}) or {}
                source_name = source_obj.get("display_name", "")
                if not source_name:
                    source_name = work.get("host_venue", {}).get("display_name", "N/A")

# Количество цитирований
                citations = work.get("cited_by_count", 0)

                # DOI
                doi = work.get("doi", "")
                doi_clean = doi.replace("https://doi.org/", "") if doi else ""

# статус ОА
                oa = work.get("open_access", {}) or {}
                is_oa = oa.get("is_oa", False)
                oa_badge = "🔓" if is_oa else ""

# тип
                work_type = work.get("type", "").replace("-", " ").title()

                lines.append(f"### {i}. {title} {oa_badge}")
                lines.append(f"> 作者: {authors_str}")
lines.append(f"> 发表: {pub_date} | {source_name} | {work_type}")
                lines.append(f"> 引用: {citations} 次")
                if doi_clean:
                    lines.append(f"> DOI: [{doi_clean}](https://doi.org/{doi_clean})")
                if is_oa:
lines.append(f">Статус: Открытый доступ")
                lines.append("")

            lines.append(f"---")
            lines.append(f"*数据来源: OpenAlex (CC0)* | *排序: 按引用数降序*")

            return ToolResponse.success(
                text="\n".join(lines),
                data={
                    "count": len(results),
                    "total": total,
                    "papers": [
                        {
                            "title": w.get("display_name"),
                            "authors": [a.get("author", {}).get("display_name", "")
                                      for a in w.get("authorships", [])],
                            "year": w.get("publication_date", "")[:4],
                            "doi": w.get("doi", ""),
                            "cited_by": w.get("cited_by_count", 0),
                            "is_oa": (w.get("open_access") or {}).get("is_oa", False),
                        }
                        for w in results
                    ]
                }
            )

        except urllib.error.HTTPError as e:
            return ToolResponse.error(
                code="NETWORK_ERROR",
                message=f"OpenAlex API 请求失败 (HTTP {e.code})"
            )
        except Exception as e:
            return ToolResponse.error(
                code="INTERNAL_ERROR",
                message=f"OpenAlex 检索出错: {str(e)}"
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="keyword", type="string",
описание="Поиск по ключевым словам, поддержка китайского и английского языков", требуется=False),
            ToolParameter(name="author", type="string",
                         description="作者姓名", required=False),
            ToolParameter(name="institution", type="string",
описание="Название учреждения, например "Университет Цинхуа", требуется=False),
            ToolParameter(name="year_from", type="string",
                         description="起始年份", required=False),
            ToolParameter(name="year_to", type="string",
                         description="截止年份", required=False),
            ToolParameter(name="open_access_only", type="boolean",
описание="Вернуть только статьи открытого доступа (Верно/Неверно)", требуется=Ложь),
            ToolParameter(name="max_results", type="integer",
описание="Максимальное количество возвращаемых результатов (по умолчанию 5, максимум 20)", требуется=False),
        ]
