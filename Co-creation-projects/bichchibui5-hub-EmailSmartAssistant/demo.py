#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Умный почтовый ассистент — демонстрационная версия
EmailSmartAssistant - Demo Version

Не требует настройки реального почтового ящика — можно сразу опробовать все функции
"""

import json
import re
from datetime import datetime, timedelta
from collections import Counter

class EmailDemo:
    def __init__(self):
        self.demo_emails = [
            {
                'id': '1',
                'subject': 'Срочно: планирование совещания по ходу проекта',
                'sender': 'manager@company.com',
                'date': '2024-01-15 09:00:00',
                'body': 'Коллеги, подготовьтесь к совещанию по ходу проекта завтра в 14:00. Необходимо подготовить итоги работы за неделю и план на следующую. Крайний срок: 2024-01-16 14:00. Пожалуйста, подтвердите участие.'
            },
            {
                'id': '2', 
                'subject': 'Запрос клиента: подробности о функциях продукта',
                'sender': 'customer@client.com',
                'date': '2024-01-15 10:30:00',
                'body': 'Здравствуйте, меня очень интересует продукция вашей компании, хочу узнать больше о функциях. Можно ли назначить демонстрацию продукта? Мой контакт: 13800138000. Жду вашего ответа.'
            },
            {
                'id': '3',
                'subject': 'Уведомление о техническом обслуживании системы',
                'sender': 'noreply@system.com', 
                'date': '2024-01-15 11:00:00',
                'body': 'Система будет обновляться 2024-01-20 с 02:00 до 04:00, в это время сервис может быть недоступен. Пожалуйста, заранее подготовьтесь. При вопросах обращайтесь в техническую поддержку.'
            },
            {
                'id': '4',
                'subject': 'Ограниченное предложение! Купите сейчас со скидкой 20%',
                'sender': 'promotion@ads.com',
                'date': '2024-01-15 12:00:00',
                'body': 'Уважаемый пользователь, у нас акция! Купите сейчас со скидкой 20%, такой шанс нельзя упускать! Перейдите по ссылке, чтобы купить.'
            },
            {
                'id': '5',
                'subject': 'Личное: план встречи на выходные',
                'sender': 'friend@personal.com',
                'date': '2024-01-15 13:00:00',
                'body': 'Привет! Давайте встретимся на ужин в эти выходные, в субботу в 19:00, в ресторане в центре города. Подтверди, пожалуйста, сможешь ли ты прийти, чтобы я забронировал столик.'
            },
            {
                'id': '6',
                'subject': 'Urgent: Meeting Request',
                'sender': 'boss@company.com',
                'date': '2024-01-15 14:00:00',
                'body': 'Hi team, we need to schedule an urgent meeting tomorrow at 3 PM to discuss the quarterly results. Please prepare your reports and confirm attendance by 5 PM today.'
            }
        ]
        
        self.classification_rules = {
            'work_keywords': ['совещание', 'проект', 'работа', 'задача', 'отчёт', 'meeting', 'project', 'work', 'task', 'urgent'],
            'customer_keywords': ['клиент', 'запрос', 'покупка', 'услуга', 'customer', 'inquiry', 'purchase', 'service'],
            'personal_keywords': ['личное', 'семья', 'друг', 'personal', 'family', 'friend', 'ужин', 'встреча'],
            'spam_keywords': ['реклама', 'продвижение', 'маркетинг', 'скидка', 'advertisement', 'promotion', 'marketing', 'акция']
        }
        
        self.reply_templates = {
            'work': {
                'ru': 'Спасибо за ваше письмо. По теме {subject} я получил(а) вашу информацию. Отвечу подробно в течение 24 часов. При срочных вопросах свяжитесь со мной.\n\nС уважением',
                'en': 'Thank you for your email regarding {subject}. I have received your information and will provide detailed feedback within 24 hours. Please feel free to contact me if there are any urgent matters.\n\nBest regards'
            },
            'customer': {
                'ru': 'Уважаемый клиент,\n\nСпасибо за интерес к нашей продукции/услугам. По вашему запросу {subject} мы назначим специалиста, который даст подробный ответ в течение 24 часов.\n\nПри других вопросах обращайтесь к нам.\n\nС уважением',
                'en': 'Dear Valued Customer,\n\nThank you for your interest in our products/services. Regarding your inquiry about {subject}, we will arrange for a professional to provide you with detailed answers within 24 hours.\n\nPlease feel free to contact us if you have any other questions.\n\nBest regards'
            },
            'general': {
                'ru': 'Здравствуйте,\n\nЯ получил(а) ваше письмо, внимательно прочитаю и отвечу в течение 24 часов.\n\nСпасибо!',
                'en': 'Hello,\n\nI have received your email and will read it carefully and reply within 24 hours.\n\nThank you!'
            }
        }

    def classify_email(self, email):
        """Классификация писем"""
        subject = email['subject'].lower()
        body = email['body'].lower()
        sender = email['sender'].lower()
        
        text_content = f"{subject} {body}"
        
        # Проверка на спам
        spam_score = sum(1 for keyword in self.classification_rules['spam_keywords'] 
                        if keyword in text_content)
        if spam_score >= 2:
            return {'type': 'spam', 'priority': 'low', 'sender_type': 'external'}
        
        # Проверка рабочих писем
        work_score = sum(1 for keyword in self.classification_rules['work_keywords'] 
                        if keyword in text_content)
        
        # Проверка клиентских писем
        customer_score = sum(1 for keyword in self.classification_rules['customer_keywords'] 
                           if keyword in text_content)
        
        # Проверка личных писем
        personal_score = sum(1 for keyword in self.classification_rules['personal_keywords'] 
                           if keyword in text_content)
        
        # Определение типа
        scores = {'work': work_score, 'customer': customer_score, 'personal': personal_score}
        email_type = max(scores, key=scores.get) if max(scores.values()) > 0 else 'other'
        
        # Определение приоритета
        priority = 'high' if any(word in text_content for word in ['срочно', 'urgent', 'asap', 'важн']) else 'medium'
        if email_type == 'spam':
            priority = 'low'
        
        # Определение типа отправителя
        if 'company.com' in sender:
            sender_type = 'colleague'
        elif 'noreply' in sender or 'no-reply' in sender:
            sender_type = 'system'
        elif email_type == 'customer':
            sender_type = 'customer'
        else:
            sender_type = 'external'
        
        return {
            'type': email_type,
            'priority': priority,
            'sender_type': sender_type
        }

    def extract_info(self, email):
        """Извлечение ключевой информации"""
        body = email['body']
        
        # Извлечение дат
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}\.\d{1,2}\.\d{4}',
            r'\d{1,2}/\d{1,2}'
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, body))
        
        # Извлечение времени
        time_patterns = [
            r'\d{1,2}:\d{2}',
            r'\d{1,2}\s*ч',
            r'\d{1,2} PM',
            r'\d{1,2} AM'
        ]
        
        times = []
        for pattern in time_patterns:
            times.extend(re.findall(pattern, body))
        
        # Извлечение контактов
        phones = re.findall(r'1[3-9]\d{9}', body)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', body)
        
        # Извлечение задач (предложения с ключевыми словами)
        todo_keywords = ['нужно', 'пожалуйста', 'подготов', 'need', 'please', 'prepare', 'подтверд']
        sentences = body.split('.')
        todos = []
        for sentence in sentences:
            if any(keyword in sentence for keyword in todo_keywords):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 5:
                    todos.append(clean_sentence)
        
        return {
            'dates': dates,
            'times': times,
            'phones': phones,
            'emails': emails,
            'todos': todos[:3]  # не более 3
        }

    def generate_reply(self, email, classification):
        """Генерация черновика ответа"""
        if classification['type'] == 'spam':
            return None
        
        # Определение языка
        is_russian = any('\u0400' <= char <= '\u04FF' for char in email['body'])
        lang = 'ru' if is_russian else 'en'
        
        # Выбор шаблона
        template_type = classification['type'] if classification['type'] in ['work', 'customer'] else 'general'
        template = self.reply_templates[template_type][lang]
        
        # Генерация ответа
        reply_content = template.format(subject=email['subject'])
        
        return {
            'to': email['sender'],
            'subject': f"Re: {email['subject']}",
            'content': reply_content,
            'language': lang,
            'template_type': template_type
        }

    def run_demo(self):
        """Запуск демонстрации"""
        print("🤖 Умный почтовый ассистент — демонстрационная версия")
        print("=" * 50)
        print(f"📧 Количество демо-писем: {len(self.demo_emails)}")
        print()
        
        results = []
        stats = {'total': 0, 'classified': 0, 'replies': 0, 'reminders': 0}
        
        for i, email in enumerate(self.demo_emails, 1):
            print(f"Обработка письма {i}/{len(self.demo_emails)}: {email['subject'][:30]}...")
            
            # Классификация
            classification = self.classify_email(email)
            stats['classified'] += 1
            
            # Извлечение информации
            extracted_info = self.extract_info(email)
            
            # Генерация ответа
            reply = self.generate_reply(email, classification)
            if reply:
                stats['replies'] += 1
            
            # Создание напоминаний
            reminders = len(extracted_info['dates']) + len(extracted_info['todos'])
            stats['reminders'] += reminders
            
            results.append({
                'email': email,
                'classification': classification,
                'extracted_info': extracted_info,
                'reply': reply,
                'reminders_count': reminders
            })
        
        stats['total'] = len(self.demo_emails)
        
        print("\n✅ Обработка завершена!")
        self.display_results(results, stats)

    def display_results(self, results, stats):
        """Отображение результатов"""
        print("\n📊 Статистика обработки:")
        print(f"  Всего писем: {stats['total']}")
        print(f"  Классифицировано: {stats['classified']}")
        print(f"  Сгенерировано ответов: {stats['replies']}")
        print(f"  Создано напоминаний: {stats['reminders']}")
        
        # Статистика по категориям
        types = [r['classification']['type'] for r in results]
        priorities = [r['classification']['priority'] for r in results]
        
        print("\n📋 Статистика классификации:")
        type_counts = Counter(types)
        for email_type, count in type_counts.items():
            print(f"  {email_type}: {count}")
        
        print("\n⚡ Статистика приоритетов:")
        priority_counts = Counter(priorities)
        for priority, count in priority_counts.items():
            print(f"  {priority}: {count}")
        
        print("\n📝 Примеры результатов обработки:")
        print("-" * 50)
        
        for i, result in enumerate(results[:3], 1):  # показать первые 3
            email = result['email']
            classification = result['classification']
            extracted = result['extracted_info']
            reply = result['reply']
            
            print(f"\nПисьмо {i}:")
            print(f"  Тема: {email['subject']}")
            print(f"  Отправитель: {email['sender']}")
            print(f"  Классификация: {classification['type']} | Приоритет: {classification['priority']}")
            
            if extracted['dates']:
                print(f"  Ключевые даты: {', '.join(extracted['dates'])}")
            if extracted['times']:
                print(f"  Время: {', '.join(extracted['times'])}")
            if extracted['todos']:
                print(f"  Задачи: {extracted['todos'][0][:50]}...")
            
            if reply:
                print(f"  Черновик ответа ({reply['language']}): {reply['content'][:80]}...")
            
            print(f"  Количество напоминаний: {result['reminders_count']}")
        
        print("\n🎉 Демонстрация завершена!")
        print("\n💡 Следующие шаги:")
        print("1. Для полного функционала запустите: jupyter notebook EmailSmartAssistant.ipynb")
        print("2. Для настройки реального почтового ящика отредактируйте: config/email_config.json")
        print("3. Для установки всех зависимостей выполните: pip install -r requirements.txt")

if __name__ == "__main__":
    demo = EmailDemo()
    demo.run_demo()
