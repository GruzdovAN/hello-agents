"""
Интерфейс ручной проверки

Используйте Gradio для создания веб-интерфейса для ручной проверки сгенерированных вопросов AIME.
"""

import json
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime
import gradio as gr


class HumanVerificationUI:
    """Интерфейс ручной проверки"""
    
    def __init__(self, data_path: str):
        """
        Интерфейс проверки инициализации
        
        Аргументы:
            data_path: путь к файлу JSON для создания данных.
        """
        self.data_path = data_path
        self.problems = self._load_problems()
        self.current_index = 0
        self.verifications = self._load_verifications()
        
    def _load_problems(self) -> List[Dict[str, Any]]:
        """Загрузить данные вопроса"""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Файл данных не существует: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_verifications(self) -> Dict[str, Any]:
        """Загрузить существующие результаты проверки"""
        verification_path = self.data_path.replace(".json", "_verifications.json")
        
        if os.path.exists(verification_path):
            with open(verification_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}
    
    def _save_verifications(self):
        """Сохранить результаты проверки"""
        verification_path = self.data_path.replace(".json", "_verifications.json")
        
        with open(verification_path, 'w', encoding='utf-8') as f:
            json.dump(self.verifications, f, ensure_ascii=False, indent=2)
    
    def get_current_problem(self) -> Tuple[str, str, str, str, str, str]:
        """Получить текущую информацию о вопросе"""
        if not self.problems:
            return "Нет названия", "", "", "", "", "0/0"

        problem = self.problems[self.current_index]
        problem_id = problem.get("id", "unknown")

        # Получить существующую информацию для проверки
        verification = self.verifications.get(problem_id, {})

        return (
            f"Вопрос {self.current_index + 1}/{len(self.problems)}",
            problem.get("problem", ""),
            f"Ответ: {problem.get('ответ', 'Н/Д')}",
            problem.get("solution", ""),
            f"Тема: {problem.get('topic', 'N/A')}",
            verification.get("comments", "")
        )
    
    def verify_problem(
        self,
        correctness: int,
        clarity: int,
        difficulty_match: int,
        completeness: int,
        status: str,
        comments: str
    ) -> str:
        """
        Подтвердить текущий вопрос
        
        Аргументы:
            правильность: оценка правильности (1-5)
            ясность: рейтинг ясности (1-5)
            Трудность_матч: оценка соответствия сложности (1-5)
            полнота: оценка полноты (1-5)
            status: статус проверки (одобрено/отклонено/нужна_переработка)
            комментарии: комментарии
        
        Возврат:
            Сообщение о результате проверки
        """
        if not self.problems:
            return "❌ Нет вопросов для проверки"
        
        problem = self.problems[self.current_index]
        problem_id = problem.get("id", "unknown")
        
        # Сохранить результаты проверки
        self.verifications[problem_id] = {
            "problem_id": problem_id,
            "scores": {
                "correctness": correctness,
                "clarity": clarity,
                "difficulty_match": difficulty_match,
                "completeness": completeness
            },
            "total_score": (correctness + clarity + difficulty_match + completeness) / 4,
            "status": status,
            "comments": comments,
            "verified_at": datetime.now().isoformat()
        }
        
        self._save_verifications()
        
        return f"✅ Проверка вопроса {problem_id} завершена! \nОбщая оценка: {self.verifications[problem_id]['total_score']:.2f}/5,0"
    
    def next_problem(self) -> Tuple[str, str, str, str, str, str]:
        """следующий вопрос"""
        if self.current_index < len(self.problems) - 1:
            self.current_index += 1
        return self.get_current_problem()
    
    def prev_problem(self) -> Tuple[str, str, str, str, str, str]:
        """Предыдущий вопрос"""
        if self.current_index > 0:
            self.current_index -= 1
        return self.get_current_problem()
    
    def get_statistics(self) -> str:
        """Получить статистику проверок"""
        if not self.verifications:
            return "Данных для проверки пока нет"
        
        total = len(self.problems)
        verified = len(self.verifications)
        
        approved = sum(1 for v in self.verifications.values() if v["status"] == "approved")
        rejected = sum(1 for v in self.verifications.values() if v["status"] == "rejected")
        needs_revision = sum(1 for v in self.verifications.values() if v["status"] == "needs_revision")
        
        avg_score = sum(v["total_score"] for v in self.verifications.values()) / verified if verified > 0 else 0
        
        return f"""
📊 Статистика проверок

Общее количество вопросов: {total}
Проверено: {проверено} ({проверено/всего*100:.1f}%)
Не проверено: {всего - проверено}

Результаты проверки:
- ✅ Автор: {утверждено}
- ❌ Отклонено: {отклонено}
- 🔄 Требуется доработка: {needs_revision}

Средний рейтинг: {avg_score:.2f}/5,0
"""
    
    def launch(self, share: bool = False):
        """Запустить интерфейс Градио"""
        with gr.Blocks(title="Ручная проверка вопросов AIME") as demo:
            gr.Markdown("# 🎯 Система ручной проверки вопросов AIME")
            gr.Markdown(f"Файл данных: `{self.data_path}`")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # область отображения вопросов
                    title = gr.Textbox(label="Текущая тема", interactive=False)
                    problem_text = gr.Textbox(label="Описание проблемы", lines=5, interactive=False)
                    answer_text = gr.Textbox(label="Отвечать", interactive=False)
                    solution_text = gr.Textbox(label="Процесс решения", lines=10, interactive=False)
                    metadata_text = gr.Textbox(label="метаданные", interactive=False)
                
                with gr.Column(scale=1):
                    # Зачетная зона
                    gr.Markdown("### 📝 Рейтинг (1-5 баллов)")
                    correctness_slider = gr.Slider(1, 5, value=3, step=1, label="правильность")
                    clarity_slider = gr.Slider(1, 5, value=3, step=1, label="ясность")
                    difficulty_slider = gr.Slider(1, 5, value=3, step=1, label="сложность сопоставления")
                    completeness_slider = gr.Slider(1, 5, value=3, step=1, label="честность")
                    
                    # Выбор статуса
                    gr.Markdown("### ✅ Статус проверки")
                    status_radio = gr.Radio(
                        choices=["approved", "rejected", "needs_revision"],
                        value="approved",
                        label="состояние"
                    )
                    
                    # Комментарий
                    comments_text = gr.Textbox(label="Комментарий", lines=3, placeholder="Пожалуйста, введите комментарий...")
                    
                    # Кнопка подтверждения
                    verify_btn = gr.Button("✅Отправить на проверку", variant="primary")
                    verify_result = gr.Textbox(label="Результаты проверки", interactive=False)
            
            # кнопки навигации
            with gr.Row():
                prev_btn = gr.Button("⬅️ Предыдущий вопрос")
                next_btn = gr.Button("Следующий вопрос ➡️")
            
            # Статистика
            with gr.Row():
                stats_text = gr.Textbox(label="Статистика проверки", lines=10, interactive=False)
                refresh_stats_btn = gr.Button("🔄 Обновить статистику")
            
            # Загрузить первоначальные вопросы
            demo.load(
                fn=self.get_current_problem,
                outputs=[title, problem_text, answer_text, solution_text, metadata_text, comments_text]
            )
            
            # Привязка событий
            verify_btn.click(
                fn=self.verify_problem,
                inputs=[correctness_slider, clarity_slider, difficulty_slider, completeness_slider, status_radio, comments_text],
                outputs=verify_result
            )
            
            next_btn.click(
                fn=self.next_problem,
                outputs=[title, problem_text, answer_text, solution_text, metadata_text, comments_text]
            )
            
            prev_btn.click(
                fn=self.prev_problem,
                outputs=[title, problem_text, answer_text, solution_text, metadata_text, comments_text]
            )
            
            refresh_stats_btn.click(
                fn=self.get_statistics,
                outputs=stats_text
            )
        
        demo.launch(share=share, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python human_verification_ui.py <путь_данных>")
        print("Пример: python human_verification_ui.pygenerated_data/aime_generated_20250110_120000.json")
        sys.exit(1)
    
    data_path = sys.argv[1]
    
    ui = HumanVerificationUI(data_path)
    ui.launch(share=False)

