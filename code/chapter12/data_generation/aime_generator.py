"""
Генератор математических вопросов AIME

Используйте платформу HelloAgents для создания математических вопросов в стиле AIME.
"""

import json
import os
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from tqdm import tqdm
from hello_agents import SimpleAgent
from hello_agents import HelloAgentsLLM
from datasets import load_dataset


class AIMEGenerator:
    """Генератор вопросов AIME"""
    
    # Слова-подсказки для генерации вопросов AIME (на английском языке)
    GENERATION_PROMPT = """You are a professional mathematics competition problem designer, skilled in creating AIME (American Invitational Mathematics Examination) style problems.

AIME Problem Characteristics:
1. Answer: An integer between 0 and 999
2. Topics: Algebra, Geometry, Number Theory, Combinatorics, Probability, etc.
3. Style: Requires multi-step reasoning, but no advanced theory
4. Difficulty: Medium to hard (similar to AIME problems 6-9)

Please generate an AIME-style mathematics problem, including:
1. Problem statement (clear and complete)
2. Answer (an integer between 0 and 999)
3. Detailed solution (including all reasoning steps)
4. Topic classification (Algebra/Geometry/Number Theory/Combinatorics/Probability)

Please output in the following JSON format, avoid using special escape characters in JSON:
```json
{
    "problem": "Problem statement in English",
    "answer": 123,
    "solution": "Detailed solution steps in English",
    "topic": "Algebra"
}
```
"""
    
    def __init__(
        self,
        llm: HelloAgentsLLM = None,
        delay_seconds: float = 1.0,
        use_reference_examples: bool = True,
        reference_dataset: str = "TianHongZXY/aime-1983-2025"
    ):
        """
        Генератор инициализации

        Аргументы:
            llm: экземпляр LLM (необязательно).
            задержание_секунд: задержка в секундах между каждой сборкой, чтобы избежать ограничений скорости API.
            use_reference_examples: следует ли использовать реальные вопросы в качестве справочных примеров.
            reference_dataset: имя набора справочных данных, значение по умолчанию — TianHongZXY/aime-1983-2025 (более 900 вопросов)
        """
        # Если llm не указан, создайте HelloAgentsLLM по умолчанию.
        if llm is None:
            self.llm = HelloAgentsLLM()
        else:
            self.llm = llm

        self.agent = SimpleAgent(
            name="AIME Generator",
            llm=self.llm,
            system_prompt="Вы профессиональный эксперт по разработке вопросов для математических соревнований."
        )
        self.delay_seconds = delay_seconds
        self.use_reference_examples = use_reference_examples
        self.reference_examples = []

        # Загрузите эталонный образец
        if use_reference_examples:
            try:
                print(f"📚 Загрузите реальный набор тестовых данных AIME: {reference_dataset}")
                # Попробуйте разные варианты разделения
                try:
                    dataset = load_dataset(reference_dataset, split="train")
                except:
                    dataset = load_dataset(reference_dataset, split="test")

                # Загрузите все вопросы для справки
                self.reference_examples = list(dataset)
                print(f"   ✓ Загружено {len(self.reference_examples)} справочных вопросов.")

                # Статистическое распределение по годам (при наличии поля года)
                year_counts = {}
                for item in self.reference_examples:
                    year = item.get('year')
                    if year:
                        year_counts[year] = year_counts.get(year, 0) + 1

                if year_counts:
                    year_range = f"{min(year_counts.keys())}-{max(year_counts.keys())}"
                    print(f"   ℹ️ Диапазон лет: {year_range}")

            except Exception as e:
                print(f"   ⚠️ Не удалось загрузить эталонный образец: {e}.")
                print(f"   ℹ️ Будет сгенерировано с использованием слов-подсказок по умолчанию.")
                self.use_reference_examples = False
    
    def generate_single(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Создать один вопрос

        Аргументы:
            max_retries: Максимальное количество повторов

        Возврат:
            данные вопроса
        """
        # Составьте слова-подсказки
        prompt = self._build_prompt()

        for attempt in range(max_retries):
            try:
                response = self.agent.run(prompt)
                return self._parse_response(response)
            except Exception as e:
                if attempt < max_retries - 1:
                    tqdm.write(f"⚠️ Генерация не удалась (попробуйте {attempt + 1}/{max_retries}), повторите попытку через {self.delay_секунды} секунд...")
                    time.sleep(self.delay_seconds)
                else:
                    tqdm.write(f"❌ Генерация не удалась, достигнуто максимальное количество повторов: {e}")
                    return self._get_default_problem()

    def _build_prompt(self) -> str:
        """Создавайте и генерируйте подсказки"""
        if not self.use_reference_examples or not self.reference_examples:
            return self.GENERATION_PROMPT

        # Случайным образом выберите эталонный образец
        example = random.choice(self.reference_examples)
        example_problem = example.get('problem', 'Example problem')
        example_answer = example.get('answer', 0)

        # Составьте слова-подсказки со справочными примерами (на английском языке)
        prompt = f"""You are a professional mathematics competition problem designer, skilled in creating AIME (American Invitational Mathematics Examination) style problems.

【Reference Example】(For style reference only, please generate a completely different problem)
Problem: {example_problem}
Answer: {example_answer}

AIME Problem Characteristics:
1. Answer: An integer between 0 and 999
2. Topics: Algebra, Geometry, Number Theory, Combinatorics, Probability, etc.
3. Style: Requires multi-step reasoning, but no advanced theory
4. Difficulty: Medium to hard (similar to AIME problems 6-9)

Please generate a **completely different** AIME-style mathematics problem, including:
1. Problem statement (clear and complete, different from the reference)
2. Answer (an integer between 0 and 999, different from the reference)
3. Detailed solution (including all reasoning steps)
4. Topic classification (Algebra/Geometry/Number Theory/Combinatorics/Probability)

Please output in the following JSON format, avoid using special escape characters in JSON:
```json
{{
    "problem": "Problem statement in English",
    "answer": 123,
    "solution": "Detailed solution steps in English",
    "topic": "Algebra"
}}
```

Important Notes:
- **Must generate a completely different problem from the reference**
- You can reference the style, but do not copy the content
- Ensure the problem is creative and original
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Анализ ответов LLM (поддерживает математические формулы LaTeX)"""
        import re

        # Извлечь часть JSON
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response.strip()

        # Используйте strict=False для json.loads для обработки экранированных символов.
        # Но этого недостаточно, нам нужна более умная обработка
        try:
            problem_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Если синтаксический анализ не удался, попробуйте исправить распространенные проблемы с экранированием LaTeX.
            # Метод: сначала замените одиночные обратные косые черты в строке двойными обратными косыми чертами (но сохраняйте экранированные).
            # Таким образом, \frac LaTeX станет \\frac, что допустимо в JSON.

            # Использование регулярных выражений: найдите все неэкранированные обратные косые черты (\, которые не являются \\)
            # и замените его на \\
            fixed_json_str = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', json_str)

            try:
                problem_data = json.loads(fixed_json_str)
            except json.JSONDecodeError:
                # Если это по-прежнему не удается, напечатайте сообщение об ошибке и выдайте
                print(f"❌ Не удалось выполнить синтаксический анализ JSON:")
                print(f"Исходный ответ: {response[:500]}...")
                print(f"Извлеченный JSON: {json_str[:500]}...")
                raise

        # Проверьте обязательные поля
        if "problem" not in problem_data or "answer" not in problem_data:
            raise ValueError("Отсутствует обязательное поле: проблема или ответ")

        # Подтвердить диапазон ответов
        answer = int(problem_data.get("answer", 0))
        if not (0 <= answer <= 999):
            print(f"⚠️ Ответ вне диапазона: {ответ}, скорректирован в диапазоне 0–999.")
            answer = max(0, min(999, answer))
            problem_data["answer"] = answer

        # Убедитесь, что существует значение по умолчанию
        problem_data.setdefault("solution", "No solution provided")
        problem_data.setdefault("topic", "Uncategorized")

        return problem_data

    def _get_default_problem(self) -> Dict[str, Any]:
        """Получить вопрос по умолчанию (используется в случае сбоя генерации)"""
        return {
            "problem": "Генерация не удалась, пожалуйста, перегенерируйте",
            "answer": 0,
            "solution": "N/A",
            "topic": "неизвестный"
        }
    
    def generate_batch(
        self,
        num_problems: int = 30,
        checkpoint_path: str = None
    ) -> List[Dict[str, Any]]:
        """
        Генерируйте вопросы пакетно

        Аргументы:
            num_problems: количество сгенерированных вопросов
            checkpoint_path: путь к файлу контрольной точки (используется для сохранения прогресса)

        Возврат:
            Список вопросов
        """
        print(f"\n🎯 Начните генерировать вопросы AIME")
        print(f"   Целевое количество: {num_problems}")
        print(f"   Создать модель: {self.llm.model}")
        print(f"   Настройка задержки: {self.delay_секунды} секунд/вопрос.")

        # Попробуйте восстановить с контрольной точки
        problems = []
        start_index = 0

        if checkpoint_path and os.path.exists(checkpoint_path):
            print(f"\n📂 Найден файл контрольной точки, пытаюсь восстановить...")
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    problems = json.load(f)
                start_index = len(problems)
                print(f"   ✓ Вопросы {start_index} восстановлены, продолжайте с {start_index + 1}")
            except Exception as e:
                print(f"   ⚠️ Не удалось восстановить: {e}, начните с нуля.")
                problems = []
                start_index = 0

        # Генерируйте вопросы (используйте tqdm для отображения прогресса)
        with tqdm(total=num_problems, initial=start_index, desc="Создание вопросов AIME", unit="вопрос") as pbar:
            last_call_time = 0  # Время последнего вызова API

            for i in range(start_index, num_problems):
                # Подсчитать время с момента последнего звонка
                if last_call_time > 0:
                    elapsed = time.time() - last_call_time
                    # Если с момента последнего вызова прошло меньше задержки_секунд, подождите
                    if elapsed < self.delay_seconds:
                        wait_time = self.delay_seconds - elapsed
                        tqdm.write(f"⏳ Подождите {wait_time:.1f} секунд, чтобы избежать ограничения скорости...")
                        time.sleep(wait_time)

                # Время начала записи
                start_time = time.time()

                # Генерировать вопросы
                problem = self.generate_single()
                problem["id"] = f"gen_aime_{i + 1}"
                problem["generated_at"] = datetime.now().isoformat()

                # Время окончания записи
                last_call_time = time.time()
                generation_time = last_call_time - start_time

                problems.append(problem)

                # Обновить описание индикатора выполнения
                pbar.set_postfix({
                    "тема": problem.get('topic', 'N/A'),
                    "Отвечать": problem.get('answer', 'N/A'),
                    "кропотливый": f"{generation_time:.1f}s"
                })
                pbar.update(1)

                # Сохранить контрольную точку
                if checkpoint_path:
                    try:
                        with open(checkpoint_path, 'w', encoding='utf-8') as f:
                            json.dump(problems, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        tqdm.write(f"⚠️ Не удалось сохранить контрольную точку: {e}.")

        print(f"\n✅ Генерация завершена! Всего вопросов: {len(problems)}")
        return problems
    
    def save_problems(
        self,
        problems: List[Dict[str, Any]],
        output_path: str
    ):
        """Сохранить вопрос в файл"""
        # Убедитесь, что каталог существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Вопрос сохранен: {output_path}")
    
    def generate_and_save(
        self,
        num_problems: int = 30,
        output_dir: str = "data_generation/generated_data"
    ) -> str:
        """Создавайте и сохраняйте вопросы"""
        # Создать выходной каталог
        os.makedirs(output_dir, exist_ok=True)

        # Очистите старые файлы контрольных точек
        for file in os.listdir(output_dir):
            if file.startswith("checkpoint_") and file.endswith(".json"):
                old_checkpoint = os.path.join(output_dir, file)
                try:
                    os.remove(old_checkpoint)
                    print(f"🗑️Удален старый файл контрольной точки: {file}.")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить старую контрольную точку: {e}.")

        # Установить путь к контрольной точке
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = os.path.join(output_dir, f"checkpoint_{timestamp}.json")

        # Генерация вопросов (с контрольными точками)
        problems = self.generate_batch(num_problems, checkpoint_path=checkpoint_path)

        # Сохранить вопрос
        output_path = os.path.join(output_dir, f"aime_generated_{timestamp}.json")
        self.save_problems(problems, output_path)

        # Формировать статистические отчеты
        self._generate_statistics_report(problems, output_dir, timestamp)

        # Удалить файл контрольной точки
        if os.path.exists(checkpoint_path):
            try:
                os.remove(checkpoint_path)
                print(f"\n🗑️ Файл контрольной точки удален.")
            except Exception as e:
                print(f"\n⚠️ Не удалось удалить файл контрольной точки: {e}.")

        return output_path
    
    def _generate_statistics_report(
        self,
        problems: List[Dict[str, Any]],
        output_dir: str,
        timestamp: str
    ):
        """Формировать статистические отчеты"""
        # Статистическое распределение тем
        topics = {}
        answers = []

        for problem in problems:
            topic = problem.get("topic", "неизвестный")
            topics[topic] = topics.get(topic, 0) + 1

            if "answer" in problem:
                answers.append(problem["answer"])
        
        # Создать отчет
        report = f"""Статистический отчет о создании вопросов #AIME

## Основная информация

- **Время генерации**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Количество вопросов**: {len(problems)}

## Распределение тем

| Тема | Количество | Пропорция |
|------|------|------|
"""
        
        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(problems) * 100
            report += f"| {topic} | {count} | {percentage:.1f}% |\n"

        if answers:
            report += f"""
## Анализ ответов

- **Средний ответ**: {sum(ответы) / len(ответы):.2f}
- **Минимальный ответ**: {мин(ответы)}
- **Максимальный ответ**: {max(ответы)}
- **Диапазон ответов**: {мин(ответы)}-{макс(ответы)}
"""
        
        report += f"""
## Список вопросов

| удостоверение личности | Тема | Ответ |
|-----|------|------|
"""

        for problem in problems[:10]:  # Показать только первые 10
            report += f"| {problem.get('id', 'N/A')} | {problem.get('topic', 'N/A')} | {problem.get('answer', 'N/A')} |\n"
        
        if len(problems) > 10:
            report += f"\n*(Отображаются только первые 10 вопросов, полный список можно просмотреть в файле JSON)*\n"
        
        report += f"""
---

*Время формирования отчета: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        # сохранить отчет
        report_path = os.path.join(output_dir, f"generation_report_{timestamp}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Статистический отчет сохранен: {report_path}")


if __name__ == "__main__":
    # Создать генератор
    generator = AIMEGenerator()
    
    # Создать 30 вопросов
    output_path = generator.generate_and_save(num_problems=30)
    
    print(f"\n ✅ Готово! Сгенерированные вопросы сохраняются в папке: {output_path}.")

