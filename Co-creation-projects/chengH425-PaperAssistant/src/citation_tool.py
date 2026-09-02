"""
Инструмент генерации академических цитат

Поддерживает три основных формата: GB/T 7714, APA 7th, MLA 9th.
"""
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class CitationTool(Tool):
    """Инструмент генерации академических цитат

    Формирует библиографическую ссылку по метаданным статьи в заданном формате.
    """

    def __init__(self):
        super().__init__(
            name="citation_generator",
            description="Генерирует академическую цитату по информации о статье в указанном формате. "
                        "Поддерживает GB/T 7714 (китайский стандарт журналов), APA 7-е издание, MLA 9-е издание. "
                        "Используйте при необходимости оформить библиографическую ссылку."
        )

    def _format_authors(self, authors_str: str, format_type: str) -> str:
        authors = [a.strip() for a in authors_str.split(",")]
        if format_type == "gbt7714":
            return ", ".join(authors)
        elif format_type == "apa":
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]}, & {authors[1]}"
            else:
                return ", ".join(authors[:-1]) + f", & {authors[-1]}"
        elif format_type == "mla":
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]}, and {authors[1]}"
            else:
                return f"{authors[0]}, et al"
        return authors_str

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        title = parameters.get("title", "")
        authors_str = parameters.get("authors", "")
        journal = parameters.get("journal", "")
        year = parameters.get("year", "")
        volume = parameters.get("volume", "")
        pages = parameters.get("pages", "")
        doi = parameters.get("doi", "")
        format_type = parameters.get("format", "gbt7714")

        if not title or not authors_str:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="Название и авторы обязательны для заполнения"
            )

        formatted_authors = self._format_authors(authors_str, format_type)

        if format_type == "gbt7714":
            citation = f"{formatted_authors}. {title}[J]. {journal}, {year}, {volume}: {pages}."
        elif format_type == "apa":
            citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume}, {pages}."
            if doi:
                citation += f" https://doi.org/{doi}"
        elif format_type == "mla":
            citation = f'{formatted_authors}. "{title}." {journal}, vol. {volume}, {year}, pp. {pages}.'
        else:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message=f"Неподдерживаемый формат цитирования: {format_type}. Доступны: gbt7714, apa, mla"
            )

        return ToolResponse.success(
            text=citation,
            data={"format": format_type, "citation": citation}
        )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="title", type="string",
                          description="Название статьи", required=True),
            ToolParameter(name="authors", type="string",
                          description="Список авторов через запятую",
                          required=True),
            ToolParameter(name="journal", type="string",
                          description="Название журнала или конференции", required=False),
            ToolParameter(name="year", type="string",
                          description="Год публикации", required=False),
            ToolParameter(name="volume", type="string",
                          description="Номер тома", required=False),
            ToolParameter(name="pages", type="string",
                          description="Страницы", required=False),
            ToolParameter(name="doi", type="string",
                          description="DOI", required=False),
            ToolParameter(name="format", type="string",
                          description="Формат цитирования: gbt7714 / apa / mla",
                          required=False),
        ]
