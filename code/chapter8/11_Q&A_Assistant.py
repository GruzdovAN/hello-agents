#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеллектуальный помощник по вопросам и ответам на документы — интеллектуальная система вопросов и ответов по документам на основе HelloAgents

Это полноценное приложение-помощник по обучению PDF, которое поддерживает:
- Загружайте PDF-документы и создавайте базу знаний
- Интеллектуальные вопросы и ответы (на основе RAG)
- Запись процесса обучения (на основе памяти)
- Обзор обучения и составление отчетов.
"""

from dotenv import load_dotenv
load_dotenv()
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from hello_agents.tools import MemoryTool, RAGTool
import gradio as gr

class PDFLearningAssistant:
    """Интеллектуальный помощник по вопросам и ответам на документы"""

    def __init__(self, user_id: str = "default_user"):
        """Инициализация помощника по обучению

        Аргументы:
            user_id: идентификатор пользователя, используемый для изоляции данных разных пользователей.
        """
        self.user_id = user_id
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Инструмент инициализации
        self.memory_tool = MemoryTool(user_id=user_id)
        self.rag_tool = RAGTool(rag_namespace=f"pdf_{user_id}")

        # Статистика обучения
        self.stats = {
            "session_start": datetime.now(),
            "documents_loaded": 0,
            "questions_asked": 0,
            "concepts_learned": 0
        }

        # Загруженный в данный момент документ
        self.current_document = None

    def load_document(self, pdf_path: str) -> Dict[str, Any]:
        """Загрузка PDF-документов в базу знаний

        Аргументы:
            pdf_path: путь к PDF-файлу

        Возврат:
            Dict: содержит результаты успеха и сообщение.
        """
        if not os.path.exists(pdf_path):
            return {"success": False, "message": f"Файл не существует: {pdf_path}"}

        start_time = time.time()

        try:
            # Используйте инструменты RAG для обработки PDF-файлов
            result = self.rag_tool.run({
                "action":"add_document",
                "file_path":pdf_path,
                "chunk_size":1000,
                "chunk_overlap":200
            })

            process_time = time.time() - start_time

            # Инструмент RAG возвращает строковое сообщение.
            self.current_document = os.path.basename(pdf_path)
            self.stats["documents_loaded"] += 1

            # Запись в обучающую память
            self.memory_tool.run({
                "action":"add",
                "content":f"Документ "{self.current_document}" загружен.",
                "memory_type":"episodic",
                "importance":0.9,
                "event_type":"document_loaded",
                "session_id":self.session_id
            })

            return {
                "success": True,
                "message": f"Загрузка успешно! (Занимает время: {process_time:.1f} секунд)",
                "document": self.current_document
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Не удалось загрузить: {str(e)}"
            }

    def ask(self, question: str, use_advanced_search: bool = True) -> str:
        """Задайте вопрос по документации

        Аргументы:
            вопрос: вопрос пользователя
            use_advanced_search: использовать ли расширенный поиск (MQE + HyDE)

        Возврат:
            ул: ответ
        """
        if not self.current_document:
            return "⚠️ Сначала загрузите документ! Используйте метод load_document() для загрузки PDF-документов."

        # Запишите вопросы в рабочую память.
        self.memory_tool.run({
            "action":"add",
            "content":f"Вопрос: {вопрос}",
            "memory_type":"working",
            "importance":0.6,
            "session_id":self.session_id
        })

        # Получить ответы с помощью RAG
        answer = self.rag_tool.run({
            "action":"ask",
            "question":question,
            "limit":5,
            "enable_advanced_search":use_advanced_search,
            "enable_mqe":use_advanced_search,
            "enable_hyde":use_advanced_search
        })

        # эпизодическая память
        self.memory_tool.run({
            "action":"add",
            "content":f"Изучение вопроса "{вопрос}"",
            "memory_type":"episodic",
            "importance":0.7,
            "event_type":"qa_interaction",
            "session_id":self.session_id
        })

        self.stats["questions_asked"] += 1

        return answer

    def add_note(self, content: str, concept: Optional[str] = None):
        """Добавить учебные заметки

        Аргументы:
            содержание: содержание заметки
            концепция: связанные концепции (необязательно)
        """
        self.memory_tool.run({
            "action":"add",
            "content":content,
            "memory_type":"semantic",
            "importance":0.8,
            "concept":concept or "general",
            "session_id":self.session_id
        })

        self.stats["concepts_learned"] += 1

    def recall(self, query: str, limit: int = 5) -> str:
        """Обзор процесса обучения

        Аргументы:
            запрос: ключевые слова запроса
            предел: количество возвращаемых результатов

        Возврат:
            ул: связанная память
        """
        result = self.memory_tool.run({
            "action":"search",
            "query":query,
            "limit":limit
        })
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику обучения

        Возврат:
            Дикт: статистика
        """
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()

        return {
            "Продолжительность сеанса": f"{длительность:.0f} секунд",
            "Загрузить документ": self.stats["documents_loaded"],
            "Количество заданных вопросов": self.stats["questions_asked"],
            "учебные заметки": self.stats["concepts_learned"],
            "текущий документ": self.current_document or "не загружен"
        }

    def generate_report(self, save_to_file: bool = True) -> Dict[str, Any]:
        """Создать отчет об обучении

        Аргументы:
            save_to_file: сохранять ли в файл

        Возврат:
            Диктант: Отчет об исследовании
        """
        # Получить сводку памяти
        memory_summary = self.memory_tool.run({"action":"summary", "limit":10})

        # Получить статистику РАГ
        rag_stats = self.rag_tool.run({"action":"stats"})

        # Создать отчет
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()
        report = {
            "session_info": {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "start_time": self.stats["session_start"].isoformat(),
                "duration_seconds": duration
            },
            "learning_metrics": {
                "documents_loaded": self.stats["documents_loaded"],
                "questions_asked": self.stats["questions_asked"],
                "concepts_learned": self.stats["concepts_learned"]
            },
            "memory_summary": memory_summary,
            "rag_status": rag_stats
        }

        # сохранить в файл
        if save_to_file:
            report_file = f"learning_report_{self.session_id}.json"
            try:
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2, default=str)
                report["report_file"] = report_file
            except Exception as e:
                report["save_error"] = str(e)

        return report





def create_gradio_ui():
    """Создать веб-интерфейс Gradio"""
    # Глобальный экземпляр помощника
    assistant_state = {"assistant": None}

    def init_assistant(user_id: str) -> str:
        """Помощник по инициализации"""
        if not user_id:
            user_id = "web_user"
        assistant_state["assistant"] = PDFLearningAssistant(user_id=user_id)
        return f"✅ Ассистент инициализирован (пользователь: {user_id})"

    def load_pdf(pdf_file) -> str:
        """Загрузить PDF-файл"""
        if assistant_state["assistant"] is None:
            return "❌ Сначала инициализируйте помощника"

        if pdf_file is None:
            return "❌ Пожалуйста, загрузите PDF-файл."

        # Файл, загруженный Gradio, является временным файловым объектом.
        pdf_path = pdf_file.name
        result = assistant_state["assistant"].load_document(pdf_path)

        if result["success"]:
            return f"✅ {result['message']}\n📄 Документ: {result['document']}"
        else:
            return f"❌ {result['message']}"

    def chat(message: str, history: List) -> Tuple[str, List]:
        """Функция чата"""
        if assistant_state["assistant"] is None:
            return "", history + [[message, "❌ Сначала инициализируйте помощника и загрузите документ."]]

        if not message.strip():
            return "", history

        # Определите, является ли это технической проблемой или проблемой проверки.
        if any(keyword in message for keyword in ["До", "узнал", "обзор", "история", "Помнить"]):
            # Обзор процесса обучения
            response = assistant_state["assistant"].recall(message)
            response = f"🧠 **Обзор обучения**\n\n{response}"
        else:
            # Технические вопросы и ответы
            response = assistant_state["assistant"].ask(message)
            response = f"💡 **Ответ**\n\n{ответ}"

        history.append([message, response])
        return "", history

    def add_note_ui(note_content: str, concept: str) -> str:
        """Добавить заметки"""
        if assistant_state["assistant"] is None:
            return "❌ Сначала инициализируйте помощника"

        if not note_content.strip():
            return "❌ Содержание заметки не может быть пустым."

        assistant_state["assistant"].add_note(note_content, concept or None)
        return f"✅ Заметка сохранена: {note_content[:50]}..."

    def get_stats_ui() -> str:
        """Получить статистику"""
        if assistant_state["assistant"] is None:
            return "❌ Сначала инициализируйте помощника"

        stats = assistant_state["assistant"].get_stats()
        result = "📊 **Статистика обучения**\n\n"
        for key, value in stats.items():
            result += f"- **{key}**: {value}\n"
        return result

    def generate_report_ui() -> str:
        """Создать отчет"""
        if assistant_state["assistant"] is None:
            return "❌ Сначала инициализируйте помощника"

        report = assistant_state["assistant"].generate_report(save_to_file=True)

        result = f"✅ Отчет об обучении создан\n\n"
        result += f"**Информация о сеансе**\n"
        result += f"- Продолжительность сеанса: {report['session_info']['duration_секунды']:.0f} секунд\n"
        result += f"– Загрузить документы: {report['learning_metrics']['documents_loaded']}\n"
        result += f"– Количество заданных вопросов: {report['learning_metrics']['questions_asked']}\n"
        result += f"– Примечания к исследованию: {report['learning_metrics']['concepts_learned']}\n"

        if "report_file" in report:
            result += f"\n💾 Отчет сохранен в: {report['report_file']}"

        return result

    # Создать интерфейс Градио
    with gr.Blocks(title="Интеллектуальный помощник по вопросам и ответам на документы", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 📚 Интеллектуальный помощник по вопросам документов и ответам

        Интеллектуальная система вопросов и ответов для документов на базе HelloAgents, поддерживающая:
        - 📄 Загружайте PDF-документы и создавайте базу знаний
        - 💬 Интеллектуальные вопросы и ответы (на основе RAG)
        - 📝 Запись учебных заметок
        - 🧠 Обзор процесса обучения
        - 📊 Создание отчетов об обучении
        """)

        with gr.Tab("🏠 Начать"):
            with gr.Row():
                user_id_input = gr.Textbox(
                    label="ID пользователя",
                    placeholder="Введите свой идентификатор пользователя (необязательно, по умолчанию — web_user)",
                    value="web_user"
                )
                init_btn = gr.Button("Помощник по инициализации", variant="primary")

            init_output = gr.Textbox(label="состояние инициализации", interactive=False)
            init_btn.click(init_assistant, inputs=[user_id_input], outputs=[init_output])

            gr.Markdown("### 📄 Загрузить PDF-документ")
            pdf_upload = gr.File(
                label="Загрузить PDF-файл",
                file_types=[".pdf"],
                type="filepath"
            )
            load_btn = gr.Button("Загрузить документ", variant="primary")
            load_output = gr.Textbox(label="Статус загрузки", interactive=False)
            load_btn.click(load_pdf, inputs=[pdf_upload], outputs=[load_output])

        with gr.Tab("💬 Интеллектуальные вопросы и ответы"):
            gr.Markdown("### Задавайте вопросы к документации или просматривайте процесс обучения")
            chatbot = gr.Chatbot(
                label="История разговоров",
                height=400,
                bubble_full_width=False
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Введите вопрос",
                    placeholder="Например: Что такое трансформатор? или Чему я научился раньше?",
                    scale=4
                )
                send_btn = gr.Button("отправлять", variant="primary", scale=1)

            gr.Examples(
                examples=[
                    "Что такое большая языковая модель?",
                    "Каковы основные компоненты архитектуры Transformer?",
                    "Как обучить большую языковую модель?",
                    "Чему я научился раньше?",
                    "Повторите, что мы узнали о механизме внимания."
                ],
                inputs=msg_input
            )

            msg_input.submit(chat, inputs=[msg_input, chatbot], outputs=[msg_input, chatbot])
            send_btn.click(chat, inputs=[msg_input, chatbot], outputs=[msg_input, chatbot])

        with gr.Tab("📝 Учебные заметки"):
            gr.Markdown("### Записывайте учебный опыт и важные понятия")
            note_content = gr.Textbox(
                label="Содержание заметки",
                placeholder="Введите свои учебные заметки...",
                lines=3
            )
            concept_input = gr.Textbox(
                label="Связанные понятия (необязательно)",
                placeholder="Например: трансформер, внимание"
            )
            note_btn = gr.Button("сохранять заметки", variant="primary")
            note_output = gr.Textbox(label="сохранить состояние", interactive=False)
            note_btn.click(add_note_ui, inputs=[note_content, concept_input], outputs=[note_output])

        with gr.Tab("📊 Изучите статистику"):
            gr.Markdown("### Просматривайте прогресс обучения и статистику")
            stats_btn = gr.Button("Обновить статистику", variant="primary")
            stats_output = gr.Markdown()
            stats_btn.click(get_stats_ui, outputs=[stats_output])

            gr.Markdown("### Создать отчет об обучении")
            report_btn = gr.Button("Создать отчет", variant="primary")
            report_output = gr.Textbox(label="Статус отчета", interactive=False)
            report_btn.click(generate_report_ui, outputs=[report_output])

    return demo


def main():
    """Основная функция — запуск веб-интерфейса Gradio."""
    print("\n" + "="*60)
    print("Интеллектуальный помощник по вопросам и ответам на документы")
    print("="*60)
    print("Запуск веб-интерфейса...\n")

    demo = create_gradio_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()

