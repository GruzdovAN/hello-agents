"""
Инструмент PDF в Markdown

Извлекайте текст из файлов PDF и конвертируйте в структурированный формат Markdown.
Поддерживает локальные файлы и URL-адреса, подходящие для чтения PDF-файлов научных статей.
"""
import os
import re
from typing import Dict, Any, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse, ToolStatus


class PDFExtractTool(Tool):
"""Инструмент PDF в Markdown

Извлекайте текстовое содержимое из файлов PDF и автоматически определяйте структуру статьи (заголовок, главы, абзацы),
и преобразован в форматированный вывод Markdown. Поддерживает локальные пути к файлам и URL-адреса.
    """

# Общие шаблоны заголовков глав статей
    SECTION_PATTERNS = [
        r'^(abstract|摘要|Abstract)$',
        r'^(introduction|引言|Introduction)$',
        r'^(related\s*work|相关工作|Related\s*Work)$',
        r'^(background|背景|Background)$',
        r'^(method|方法|Method(ology|s)?)$',
        r'^(experiment|实验|Experiment(s|al\s*setup)?)$',
        r'^(result|结果|Result(s)?(\s*and\s*analysis)?)$',
        r'^(discussion|讨论|Discussion)$',
        r'^(conclusion|结论|Conclusion(\s*and\s*future\s*work)?)$',
        r'^(reference|参考文献|Reference(s)?)$',
        r'^(appendix|附录|Appendix)$',
        r'^(evaluation|评估|Evaluation)$',
        r'^(implementation|实现|Implementation)$',
        r'^(limitation|局限|Limitation(s)?)$',
    ]

    def __init__(self):
        super().__init__(
            name="pdf_extract",
            description="从 PDF 文件中提取文本并转换为 Markdown 格式。"
«Автоматически распознавать структуру документа (название, главы, абзацы)»
«Очистите PDF-файлы от помех, таких как разрывы строк и номера страниц».
«Поддерживает локальные пути к файлам PDF или URL-адреса PDF».
                        "适合将论文 PDF 转为 Markdown 后用于进一步分析。"
        )

    def _extract_raw_text(self, file_path: str, start_page: int = 1,
                           end_page: int = -1) -> str:
"""Используйте PyPDF2 для извлечения необработанного текста"""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("请安装 PyPDF2: pip install PyPDF2")

        reader = PdfReader(file_path)
        total_pages = len(reader.pages)

        if end_page == -1 or end_page > total_pages:
            end_page = total_pages

        all_text = []
        for i in range(start_page - 1, min(end_page, total_pages)):
            page = reader.pages[i]
            text = page.extract_text()
            if text:
                all_text.append(text)

        if not all_text:
            return ""

        return "\n".join(all_text)

    def _clean_text(self, text: str) -> str:
"""Чистый шум при извлечении PDF"""
# Удаление отдельных строк номеров страниц
        text = re.sub(r'^\d{1,4}$', '', text, flags=re.MULTILINE)
# Удалить общие шаблоны верхнего и нижнего колонтитула (например, «имя автора/название журнала», повторяющееся на страницах)
        text = re.sub(r'^\d+\s*\n', '\n', text, flags=re.MULTILINE)
# Объединяем лишние последовательные пустые строки
        text = re.sub(r'\n{4,}', '\n\n\n', text)
# Очистка конечных пробелов
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
# Удалить символы нулевой ширины
        text = re.sub(r'[​‌‍﻿]', '', text)
        return text.strip()

    def _fix_broken_lines(self, text: str) -> str:
"""Исправлены распространенные проблемы с переносом строк при извлечении PDF-файлов.

Извлечение PDF часто приводит к ненужным разрывам строк в середине абзацев.
Объедините строки, которые не заканчиваются знаками препинания/двоеточия, и следующая строка начинается со строчной буквы.
        """
        lines = text.split('\n')
        fixed = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                fixed.append('')
                i += 1
                continue

# Если текущая строка не заканчивается точкой/вопросительным знаком/восклицательным знаком/двоеточием/кавычкой,
# и следующая строка существует и не начинается с заглавной буквы, цифры или пустой строки → объединить
            if (i + 1 < len(lines) and
                not re.search(r'[.!?:\"»)]$', line) and
len(line) > 20 и # Короткие строки (заголовки) не объединяются
                lines[i + 1].strip() and
                not re.match(r'^[A-Z0-9#]', lines[i + 1].strip()) and
                not re.match(r'^\[', lines[i + 1].strip())):

                fixed.append(line + ' ' + lines[i + 1].strip())
                i += 2
            else:
                fixed.append(line)
                i += 1

        return '\n'.join(fixed)

    def _to_markdown(self, text: str) -> str:
"""Конвертируйте очищенный текст в Markdown"""
        lines = text.split('\n')
        md_lines = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
# Пустые строки = разрывы абзацев
                md_lines.append('')
                continue

# Пропустить чистый номер страницы и короткие числовые строки
            if re.match(r'^\d{1,4}$', stripped):
                continue

# Название главы с номером теста: 1. / 1.1 / 2.3.1 и т. д.
            numbered_heading = re.match(
                r'^(\d{1,2}(?:\.\d{1,2}){0,2})\s+(.+)', stripped
            )
            if numbered_heading and len(stripped) < 80:
                depth = numbered_heading.group(1).count('.') + 1
                prefix = '#' * min(depth + 1, 4)  # 最多 ####
                md_lines.append(f'\n{prefix} {stripped}')
                continue

# Обнаружение распространенных названий академических глав
            is_section = False
            for pattern in self.SECTION_PATTERNS:
                if re.match(pattern, stripped, re.IGNORECASE):
                    is_section = True
                    break
            if is_section and len(stripped) < 60:
                md_lines.append(f'\n## {stripped}')
                continue

# Обнаружение коротких строк заглавными буквами → наиболее вероятные заголовки
            if (stripped.isupper() and len(stripped) < 60 and
                len(stripped.split()) >= 2):
                md_lines.append(f'\n### {stripped.title()}')
                continue

# Элементы контрольного списка
            list_match = re.match(r'^[\-\•\*\d+]\s{1,3}', stripped)
            if list_match:
                md_lines.append(f'- {stripped[list_match.end():]}')
                continue

# Обычный абзац
            md_lines.append(stripped)

# Объединить результаты
        result = '\n'.join(md_lines)
# Очистим лишние пустые строки
        result = re.sub(r'\n{3,}', '\n\n', result)
# Убедитесь, что до и после заголовка есть пустые строки
        result = re.sub(r'([^\n])\n(#{1,4}\s)', r'\1\n\n\2', result)
        return result.strip()

    def _download_pdf(self, url: str, save_dir: str = "outputs") -> str:
"""Загрузка удаленных PDF-файлов"""
        import urllib.request

        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.join(save_dir, f"downloaded_{abs(hash(url))}.pdf")

        req = urllib.request.Request(url, headers={"User-Agent": "PaperAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(filename, "wb") as f:
                f.write(resp.read())

        return filename

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        file_path = parameters.get("file_path", "")
        url = parameters.get("url", "")
        start_page = parameters.get("start_page", 1)
        end_page = parameters.get("end_page", -1)
        max_chars = parameters.get("max_chars", 0) or 0  # 0 = 不限制

        if not file_path and not url:
            return ToolResponse.error(
                code="INVALID_PARAM",
                message="请提供 file_path（本地文件路径）或 url（PDF 链接）"
            )

        try:
            if url:
                file_path = self._download_pdf(url)

            if not os.path.exists(file_path):
                return ToolResponse.error(
                    code="NOT_FOUND",
                    message=f"文件不存在: {file_path}"
                )

# 1. Извлечь исходный текст
            raw_text = self._extract_raw_text(file_path, start_page, end_page)

            if not raw_text:
                return ToolResponse.error(
                    code="INVALID_FORMAT",
message="Не удалось извлечь текст из PDF. Это может быть отсканированный PDF-файл (формат изображения). Для предварительной обработки рекомендуется использовать инструмент оптического распознавания символов."
                )

# 2. Очистить → 3. Исправить разрывы строк → 4. Преобразовать в Markdown
            cleaned = self._clean_text(raw_text)
            fixed = self._fix_broken_lines(cleaned)
            markdown = self._to_markdown(fixed)

# Необязательное усечение (без ограничений, если max_chars=0)
            truncated = max_chars > 0 and len(markdown) > max_chars
            if truncated:
                markdown = markdown[:max_chars]
                last_break = max(markdown.rfind('\n\n'), markdown.rfind('\n'))
                if last_break > max_chars * 0.8:
                    markdown = markdown[:last_break]
markdown += f"\n\n> *Содержимое усечено (показаны первые символы: {max_chars}). Установите значение 0, чтобы получить полный текст.*"

            stats = {
                "total_chars": len(markdown),
                "word_count": len(markdown.split()),
                "line_count": len(markdown.split("\n")),
"pages": f"{start_page}-{end_page if end_page != -1 else '全部'}",
                "truncated": truncated,
                "format": "markdown"
            }

            return ToolResponse.success(text=markdown, data=stats)

        except ImportError as e:
            return ToolResponse.error(
                code="INTERNAL_ERROR",
                message=str(e)
            )
        except Exception as e:
            return ToolResponse.error(
                code="EXECUTION_ERROR",
                message=f"PDF 转 Markdown 失败: {str(e)}"
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path", type="string",
описание="Локальный путь к PDF-файлу",
                required=False
            ),
            ToolParameter(
                name="url", type="string",
                description="PDF 文件 URL（如 arXiv 论文链接）",
                required=False
            ),
            ToolParameter(
                name="start_page", type="integer",
описание="Номер стартовой страницы (по умолчанию 1)",
                required=False
            ),
            ToolParameter(
                name="end_page", type="integer",
описание="Номер конечной страницы (-1 означает все)",
                required=False
            ),
            ToolParameter(
                name="max_chars", type="integer",
                description="最大返回字符数（0=不限制，默认 0）",
                required=False
            ),
        ]
