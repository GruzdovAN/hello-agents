"""Экспорт колонки"""

import os
import json
from typing import Dict, Any
from datetime import datetime


class ColumnExporter:
    """Экспорт колонки в файлы"""

    @staticmethod
    def export_to_files(column_data: Dict[str, Any], output_dir: str = "column_output"):
        """
        Экспорт колонки в файлы

        Args:
            column_data: данные колонки
            output_dir: каталог вывода
        """
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n{'='*70}")
        print(f"▸ Экспорт файлов колонки...")
        print(f"{'='*70}\n")

        json_path = os.path.join(output_dir, 'column_data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(column_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"▸ Сохранены данные: {json_path}")

        for article in column_data['articles']:
            safe_title = "".join(c for c in article['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{article['id']}_{safe_title}.md"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(article['content'])

                f.write(f"\n\n---\n\n")
                f.write(f"## Метаданные статьи\n\n")
                f.write(f"- **ID статьи**: {article['id']}\n")
                f.write(f"- **Слов**: {article['word_count']}\n")
                f.write(f"- **Балл ревью**: {article['metadata'].get('review_score', 'N/A')}\n")
                f.write(f"- **Оценка ревью**: {article['metadata'].get('review_grade', 'N/A')}\n")

                if article.get('has_revisions'):
                    f.write(f"- **Число правок**: {article['revision_count']}\n")
                    if 'revision_summary' in article['metadata']:
                        f.write(f"- **Основные правки**:\n")
                        for change in article['metadata']['revision_summary'].get('major_changes', []):
                            f.write(f"  - {change}\n")

            print(f"▸ Сохранена статья: {filepath}")

        report_path = os.path.join(output_dir, 'REPORT.md')
        ColumnExporter._export_report(column_data, report_path)
        print(f"▸ Сохранён отчёт: {report_path}")

        print(f"\n{'='*70}")
        print(f"▸ Экспорт завершён: {output_dir}")
        print(f"{'='*70}\n")

    @staticmethod
    def _export_report(column_data: Dict[str, Any], filepath: str):
        """Экспорт отчёта статистики"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {column_data['column_info']['title']}\n\n")
            f.write(f"## Информация о колонке\n\n")
            f.write(f"- **Описание**: {column_data['column_info']['description']}\n")
            f.write(f"- **Аудитория**: {column_data['column_info']['target_audience']}\n")
            f.write(f"- **Число статей**: {column_data['column_info']['topic_count']}\n\n")

            f.write(f"## Статистика контента\n\n")
            stats = column_data['statistics']
            f.write(f"- **Всего слов**: {stats['total_words']:,}\n")
            f.write(f"- **Среднее на статью**: {stats['avg_words_per_article']:,} слов\n")
            f.write(f"- **Узлов контента**: {stats['total_nodes']}\n")

            if 'approval_rate' in stats:
                f.write(f"- **Прошли без правок**: {stats.get('approved_nodes', 0)} ({stats['approval_rate']})\n")
                f.write(f"- **С правками**: {stats.get('revised_nodes', 0)} ({stats['revision_rate']})\n")

            if 'quality_report' in column_data:
                f.write(f"\n## Отчёт качества\n\n")
                quality = column_data['quality_report']
                f.write(f"- **Средний балл**: {quality['average_score']:.1f}/100\n")
                f.write(f"- **Диапазон**: {quality['min_score']}-{quality['max_score']}\n")
                f.write(f"- **Оценённых узлов**: {quality['total_evaluated']}\n\n")

                f.write(f"### Распределение оценок\n\n")
                for grade, count in quality['grade_distribution'].items():
                    if count > 0:
                        percentage = count / quality['total_evaluated'] * 100 if quality['total_evaluated'] > 0 else 0
                        f.write(f"- **{grade}**: {count} ({percentage:.1f}%)\n")

            if 'agent_modes' in column_data:
                f.write(f"\n## Режимы агентов\n\n")
                modes = column_data['agent_modes']
                f.write(f"- **Planner**: {modes.get('planner', 'N/A')}\n")
                f.write(f"- **Writer**: {modes.get('writer', 'N/A')}\n")

            if 'creation_stats' in column_data:
                creation = column_data['creation_stats']
                if creation.get('start_time') and creation.get('end_time'):
                    start_time = creation['start_time']
                    end_time = creation['end_time']

                    if isinstance(start_time, str):
                        try:
                            start_time = datetime.fromisoformat(start_time)
                            end_time = datetime.fromisoformat(end_time)
                        except Exception:
                            pass

                    if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                        duration = (end_time - start_time).total_seconds()

                        f.write(f"\n## Статистика создания\n\n")
                        f.write(f"- **Начало**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"- **Конец**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"- **Длительность**: {duration:.1f} сек ({duration/60:.1f} мин)\n")

                f.write(f"- **Генераций**: {creation.get('total_generations', 0)}\n")
                if creation.get('total_reviews') > 0:
                    f.write(f"- **Ревью**: {creation.get('total_reviews')}\n")
                if creation.get('total_revisions') > 0:
                    f.write(f"- **Правок**: {creation.get('total_revisions')}\n")

            f.write(f"\n## Список статей\n\n")
            for idx, article in enumerate(column_data['articles'], 1):
                f.write(f"{idx}. **{article['title']}** ({article['word_count']} слов)\n")

                meta = article.get('metadata', {})
                if 'agent_mode' in meta:
                    f.write(f"   - Режим: {meta['agent_mode']}\n")

                if 'review_score' in meta:
                    f.write(f"   - Балл: {meta['review_score']}/100\n")

                f.write("\n")
