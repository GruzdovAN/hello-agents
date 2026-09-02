#!/usr/bin/env python3
"""
Многосторонние исторические дебаты: столкновение точек зрения → Окончательный синтез.

По умолчанию **Взаимодействие**: Будет задан вопрос о теме, является ли она сетевым приложением и нужно ли подтверждать запуск.
Неинтерактивный режим одним щелчком мыши: добавьте -y (или --yes), чтобы решить проблемы с командной строкой.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from historical_review.cli_interactive import prompt_topic, prompt_yes_no
from historical_review.debate_orchestrator import run_historical_debate

DEFAULT_TOPIC = (
«Изменения ворот Сюаньу: как написать повествование официальной истории? Если мы объединим мощь дворца и среду написания гражданской истории того времени»,
«Какие записи кажутся странными? Могут ли неофициальные истории и зарубежные материалы выявить пробелы?»
)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="多角色历史辩论（官修/野史/政治语境/域外/蹊跷辨析 → 综合）",
    )
    parser.add_argument(
        "topic",
        nargs="?",
        default=None,
help="Исторические вопросы; не задавать вопросы в интерактивном режиме",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
help="Неинтерактивно: не спрашивайте, используйте параметры и значения по умолчанию напрямую (подходит для скриптов/автоматизации)",
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
help="Не сканировать приложения вики/поиска (если в интерактивном режиме эта опция не указана, вам все равно будет задан вопрос, включить ли ее)",
    )
    parser.add_argument(
        "--debate-temp",
        type=float,
        default=0.72,
help="Температура колеса дебатов",
    )
    parser.add_argument(
        "--synth-temp",
        type=float,
        default=0.22,
help="Конечная комплексная температура",
    )
    args = parser.parse_args()

    topic = args.topic
    use_evidence = not args.no_evidence

    if args.yes:
        if topic is None or not str(topic).strip():
            topic = DEFAULT_TOPIC
        use_evidence = not args.no_evidence
    else:
        print("=" * 56)
print("Многосимвольные исторические дебаты - сначала подтвердите этот вариант (добавьте -y, чтобы пропустить этот процесс)")
        print("=" * 56)
        if topic is None or not str(topic).strip():
            topic = prompt_topic(DEFAULT_TOPIC)
        else:
print(f"\nТема (из командной строки): {topic}\n")

        if args.no_evidence:
            use_evidence = False
            print("已指定 --no-evidence：不抓取维基/检索附录。\n")
        else:
use_evidence = Prompt_yes_no("Хотите ли вы включить вики и поиск в качестве приложения для текстовых исследований?", по умолчанию=True)
            print()

        if not prompt_yes_no(
«Приходится вызывать последовательно: 5 символов в первом раунде + 1 резюме секретаря + 5 символов во втором раунде + 1 окончательный синтез (около 12 запросов LLM), подтвердить начало?»,
            default=True,
        ):
print("Отменено.")
            sys.exit(0)
        print()

    report = run_historical_debate(
        str(topic).strip(),
        use_evidence_bundle=use_evidence,
        debate_temperature=args.debate_temp,
        synthesizer_temperature=args.synth_temp,
    )
    print(report)


if __name__ == "__main__":
    main()
