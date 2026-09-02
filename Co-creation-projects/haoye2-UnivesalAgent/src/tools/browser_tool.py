import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import time
import re
import html

class BrowserTool:
    name = "browser_search"
    description = "Выполняет веб-поиск (поддерживаются несколько поисковых систем и извлечение контента)"
    
    def get_parameters(self):
        return {
            "input": {"type": "str", "description": "Ключевые слова для поиска", "required": True}
        }

    def _is_valid_result(self, title, url):
        """Проверяет валидность результата поиска"""
        if not title or len(title.strip()) < 3:
            return False
        
        # Фильтрация навигационных ссылок и бессмысленного контента
        skip_keywords = [
            "next", "previous", "more", "about", "help", "settings",
            "privacy", "terms", "feedback", "donate", "install",
            "download", "login", "register", "sign in", "sign up"
        ]
        
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in skip_keywords):
            return False
        
        # Фильтрация рекламы и промо-ссылок
        ad_indicators = ["ad", "sponsored", "promotion", "реклама", "промо"]
        if any(indicator in title_lower for indicator in ad_indicators):
            return False
        
        return True

    def _clean_text(self, text):
        """Очищает текстовое содержимое"""
        if not text:
            return ""
        
        # Удаление лишних пробельных символов
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Удаление специальных символов
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', '', text)
        
        return text[:200]  # ограничение длины

    def _search_searx(self, query, limit=5):
        """Использует несколько экземпляров поисковых систем — стабильная версия с приоритетом CJK-запросов"""
        # Подбор стабильных поисковых систем
        search_instances = [
            {
                "name": "Searx.xyz",
                "url": "https://searx.xyz/search",
                "timeout": 10,
                "type": "searx"
            },
            {
                "name": "Searx.be",
                "url": "https://searx.be/search",
                "timeout": 10,
                "type": "searx"
            },
            {
                "name": "Поиск Brave",
                "url": "https://search.brave.com/search",
                "timeout": 8,
                "type": "brave"
            },
            {
                "name": "Ecosia",
                "url": "https://www.ecosia.org/search",
                "timeout": 8,
                "type": "ecosia"
            },
            {
                "name": "Qwant",
                "url": "https://www.qwant.com",
                "timeout": 8,
                "type": "qwant"
            }
        ]
        
        for instance in search_instances:
            try:
                print(f"🔍 Пробуем {instance['name']}...")
                result = self._try_search_instance(instance, query, limit)
                if result and len(result) > 0:
                    print(f"✅ {instance['name']}: поиск успешен, найдено {len(result)} результатов")
                    return result, True
                    
            except Exception as e:
                print(f"⚠️ {instance['name']} не удался: {str(e)[:50]}")
                continue  # тихий сбой, быстрое переключение
        
        # Быстрый переход к поисковым подсказкам
        print("🔗 Все поисковые системы недоступны, предлагаем варианты поиска")
        return self._get_search_suggestions(query), True

    def _try_search_instance(self, instance, query, limit):
        """Пробует один экземпляр поисковой системы"""
        if instance['type'] == 'searx':
            return self._try_searx_instance(instance, query, limit)
        elif instance['type'] == 'duckduckgo':
            return self._try_duckduckgo_instance(instance, query, limit)
        elif instance['type'] == 'startpage':
            return self._try_startpage_instance(instance, query, limit)
        elif instance['type'] == 'qwant':
            return self._try_qwant_instance(instance, query, limit)
        elif instance['type'] == 'brave':
            return self._try_brave_instance(instance, query, limit)
        elif instance['type'] == 'ecosia':
            return self._try_ecosia_instance(instance, query, limit)
        else:
            return None

    def _try_searx_instance(self, instance, query, limit):
        """Пробует экземпляр Searx — оптимизировано для CJK-запросов"""
        # Определяем, содержит ли запрос иероглифы CJK
        is_cjk = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        params = {
            'q': query,
            'format': 'json',
            'engines': 'google,bing,duckduckgo,yandex' if not is_cjk else 'google,bing,yandex,baidu',
            'language': 'zh-CN' if is_cjk else 'auto'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8" if is_cjk else "en-US,en;q=0.9"
        }
        
        try:
            response = requests.get(
                instance['url'], 
                params=params, 
                headers=headers, 
                timeout=instance['timeout']
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results = []
                    
                    for item in data.get('results', [])[:limit]:
                        title = self._clean_text(item.get('title', ''))
                        url = item.get('url', '')
                        content = item.get('content', '')
                        
                        if self._is_valid_result(title, url):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': self._clean_text(content)[:200],
                                'source': f"{instance['name']}/{item.get('engine', 'unknown')}"
                            })
                    
                    return results if results else None
                except Exception as e:
                    print(f"⚠️ Не удалось разобрать ответ Searx: {str(e)[:50]}")
                    return None
            else:
                print(f"⚠️ Searx вернул код состояния: {response.status_code}")
                return None
        except requests.Timeout:
            print(f"⚠️ {instance['name']}: превышено время ожидания запроса")
            return None
        except Exception as e:
            print(f"⚠️ {instance['name']}: ошибка запроса: {str(e)[:50]}")
            return None

    def _try_duckduckgo_instance(self, instance, query, limit):
        """Пробует экземпляр DuckDuckGo"""
        params = {
            'q': query,
            'kl': 'cn-zh'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        response = requests.get(
            instance['url'], 
            params=params, 
            headers=headers, 
            timeout=instance['timeout']
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._extract_duckduckgo_results_from_soup(soup, limit)
        
        return None

    def _try_startpage_instance(self, instance, query, limit):
        """Пробует экземпляр Startpage"""
        params = {
            'query': query,
            'cat': 'web',
            'pl': 'ext-ff',
            'extVersion': '1.3.0'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        response = requests.get(
            instance['url'], 
            params=params, 
            headers=headers, 
            timeout=instance['timeout']
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._extract_startpage_results(soup, limit)
        
        return None

    def _try_qwant_instance(self, instance, query, limit):
        """Пробует экземпляр Qwant"""
        params = {
            'q': query,
            't': 'web',
            'locale': 'zh_CN'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        response = requests.get(
            instance['url'], 
            params=params, 
            headers=headers, 
            timeout=instance['timeout']
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._extract_qwant_results(soup, limit)
        
        return None

    def _try_brave_instance(self, instance, query, limit):
        """Пробует экземпляр поиска Brave"""
        params = {
            'q': query,
            'source': 'web'
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        
        try:
            response = requests.get(
                instance['url'], 
                params=params, 
                headers=headers, 
                timeout=instance['timeout']
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Извлечение результатов Brave (может потребоваться настройка под актуальную HTML-структуру)
                results = []
                result_divs = soup.find_all('div', class_=['result', 'web-result'])
                
                for div in result_divs[:limit]:
                    title_elem = div.find('a') or div.find('h2')
                    snippet_elem = div.find('p') or div.find('span', class_='snippet')
                    
                    if title_elem:
                        title = self._clean_text(title_elem.get_text())
                        url = title_elem.get('href', '')
                        snippet = self._clean_text(snippet_elem.get_text()) if snippet_elem else ''
                        
                        if self._is_valid_result(title, url):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet[:200],
                                'source': 'Brave'
                            })
                
                return results if results else None
        except Exception:
            return None
        
        return None

    def _try_ecosia_instance(self, instance, query, limit):
        """Пробует экземпляр поиска Ecosia"""
        params = {
            'q': query
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        
        try:
            response = requests.get(
                instance['url'], 
                params=params, 
                headers=headers, 
                timeout=instance['timeout']
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Извлечение результатов Ecosia (может потребоваться настройка под актуальную HTML-структуру)
                results = []
                result_divs = soup.find_all('div', class_=['result', 'web-result', 'result__body'])
                
                for div in result_divs[:limit]:
                    title_elem = div.find('a') or div.find('h2')
                    snippet_elem = div.find('p') or div.find('span', class_='result__snippet')
                    
                    if title_elem:
                        title = self._clean_text(title_elem.get_text())
                        url = title_elem.get('href', '')
                        snippet = self._clean_text(snippet_elem.get_text()) if snippet_elem else ''
                        
                        if self._is_valid_result(title, url):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet[:200],
                                'source': 'Ecosia'
                            })
                
                return results if results else None
        except Exception:
            return None
        
        return None

    def _extract_duckduckgo_results_from_soup(self, soup, limit):
        """Извлекает результаты из HTML DuckDuckGo"""
        results = []
        
        # Поиск результатов
        result_divs = soup.find_all('div', class_='result')
        
        for div in result_divs[:limit]:
            title_elem = div.find('a', class_='result__a')
            snippet_elem = div.find('a', class_='result__snippet')
            
            if title_elem:
                title = self._clean_text(title_elem.get_text())
                url = title_elem.get('href', '')
                snippet = self._clean_text(snippet_elem.get_text()) if snippet_elem else ''
                
                if self._is_valid_result(title, url):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet[:200],
                        'source': 'DuckDuckGo'
                    })
        
        return results

    def _extract_startpage_results(self, soup, limit):
        """Извлекает результаты из HTML Startpage"""
        results = []
        
        # Поиск результатов
        result_divs = soup.find_all('div', class_='w-gl__result')
        
        for div in result_divs[:limit]:
            title_elem = div.find('h3')
            link_elem = title_elem.find('a') if title_elem else None
            snippet_elem = div.find('p', class_='w-gl__description')
            
            if link_elem:
                title = self._clean_text(link_elem.get_text())
                url = link_elem.get('href', '')
                snippet = self._clean_text(snippet_elem.get_text()) if snippet_elem else ''
                
                if self._is_valid_result(title, url):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet[:200],
                        'source': 'Startpage'
                    })
        
        return results

    def _extract_qwant_results(self, soup, limit):
        """Извлекает результаты из HTML Qwant"""
        results = []
        
        # Поиск результатов
        result_divs = soup.find_all('div', class_='result')
        
        for div in result_divs[:limit]:
            title_elem = div.find('a', class_='result--web')
            snippet_elem = div.find('p', class_='result__desc')
            
            if title_elem:
                title = self._clean_text(title_elem.get_text())
                url = title_elem.get('href', '')
                snippet = self._clean_text(snippet_elem.get_text()) if snippet_elem else ''
                
                if self._is_valid_result(title, url):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet[:200],
                        'source': 'Qwant'
                    })
        
        return results

    def _extract_duckduckgo_results(self, soup, limit=5):
        """Извлекает результаты поиска DuckDuckGo"""
        results = []
        
        # DuckDuckGo часто возвращает код 202 и требует JavaScript-рендеринг
        # Пытаемся извлечь любую полезную информацию из HTML
        
        # Способ 1: поиск всех внешних ссылок
        all_links = soup.find_all('a', href=True)
        external_links = []
        
        for link in all_links:
            href = link.get('href', '')
            title = self._clean_text(link.get_text(strip=True))
            
            # Фильтрация внешних ссылок (не внутренних ссылок DuckDuckGo)
            if (href and 
                not href.startswith('javascript:') and
                not href.startswith('#') and
                'duckduckgo.com' not in href and
                len(title) > 3 and
                self._is_valid_result(title, href)):
                
                external_links.append({
                    'title': title,
                    'url': href,
                    'snippet': '',
                    'link_element': link
                })
        
        # Способ 2: если внешних ссылок мало — извлечение из текста страницы
        if len(external_links) < 2:
            print("⚠️ Мало внешних ссылок, пробуем извлечь текст")
            
            # Поиск основного текстового содержимого страницы
            text_content = soup.get_text()
            
            # Извлечение URL по шаблону
            import re
            url_pattern = r'https?://[^\s<>"\'()]+'
            urls = re.findall(url_pattern, text_content)
            
            for url in urls[:limit]:
                # Извлечение возможного заголовка из URL
                domain = url.split('/')[2] if '/' in url else url
                title = domain.replace('www.', '').title()
                
                if self._is_valid_result(title, url):
                    external_links.append({
                        'title': title,
                        'url': url,
                        'snippet': f'Источник: {domain}',
                        'link_element': None
                    })
        
        # Способ 3: если результатов всё ещё мало — поисковые подсказки
        if len(external_links) < 2:
            print("⚠️ Результатов мало, предлагаем варианты поиска")
            
            suggestions = [
                {
                    'title': f'Поиск в Google: «{self.last_query}»',
                    'url': f'https://www.google.com/search?q={self.last_query}',
                    'snippet': 'Поисковая система Google',
                    'link_element': None
                },
                {
                    'title': f'Поиск в Bing: «{self.last_query}»',
                    'url': f'https://www.bing.com/search?q={self.last_query}',
                    'snippet': 'Поисковая система Bing',
                    'link_element': None
                }
            ]
            external_links.extend(suggestions)
        
        # Дедупликация и ограничение числа результатов
        seen_urls = set()
        unique_results = []
        
        for result in external_links:
            if result['url'] and result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        return unique_results

    def _extract_content_from_url(self, url, max_length=300):
        """Извлекает основное содержимое по URL"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return "Не удалось получить содержимое"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Удаление тегов script и style
            for script in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement"]):
                script.decompose()
            
            # Стратегия интеллектуального извлечения контента
            content = self._extract_main_content(soup)
            
            if not content:
                content = soup.get_text(strip=True)
            
            # Очистка и оптимизация содержимого
            content = self._clean_and_format_content(content)
            
            return content[:max_length] + "..." if len(content) > max_length else content
            
        except Exception as e:
            return f"Ошибка извлечения содержимого: {str(e)[:50]}"

    def _extract_main_content(self, soup):
        """Интеллектуально извлекает основное содержимое страницы"""
        # Стратегия приоритетов: от конкретного к общему
        extraction_strategies = [
            # 1. Теги, связанные со статьями
            ['article', 'main article', '.article-content', '.post-content'],
            # 2. Основная область контента
            ['main', '.main', '.content', '.main-content'],
            # 3. Распространённые классы контента
            ['.entry-content', '.post-body', '.article-body', '.content-area'],
            # 4. Общие контейнеры
            ['.container', '.wrapper', '.page-content'],
            # 5. Последняя попытка — body
            ['body']
        ]
        
        for strategy in extraction_strategies:
            for selector in strategy:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    # Проверка качества контента
                    if self._is_quality_content(content):
                        return content
        
        return ""

    def _is_quality_content(self, content):
        """Проверяет качество контента"""
        if not content or len(content) < 50:
            return False
        
        # Фильтрация навигации и меню
        nav_keywords = ['навигация', 'меню', 'главная', 'вход', 'регистрация', 'поиск', 'контакты', 'о нас', 'privacy', 'terms', 'home', 'login', 'register', 'contact', 'about']
        content_lower = content.lower()
        
        for keyword in nav_keywords:
            if keyword in content_lower:
                return False
        
        # Проверка наличия осмысленных предложений
        sentences = re.split(r'[.!?。]', content)
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return len(meaningful_sentences) >= 2

    def _clean_and_format_content(self, content):
        """Очищает и форматирует содержимое"""
        if not content:
            return ""
        
        # Удаление лишних пробелов
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Удаление специальных символов, сохранение пунктуации
        content = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', '', content)
        
        # Удаление повторяющихся переводов строк и пробелов
        content = re.sub(r'\n\s*\n', '\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Извлечение первых осмысленных предложений
        sentences = re.split(r'[.!?。]', content)
        meaningful_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 100:  # разумная длина предложения
                meaningful_sentences.append(sentence)
                if len(meaningful_sentences) >= 3:  # не более 3 предложений
                    break
        
        return '. '.join(meaningful_sentences)

    def _enhance_search_results(self, results, limit=3):
        """Улучшает результаты поиска, извлекая превью контента"""
        enhanced_results = []
        
        for i, result in enumerate(results):
            if i >= limit:  # улучшаем только первые результаты
                break
            
            if result['url'] and result['url'].startswith('http'):
                print(f"📄 Извлечение контента: {result['title'][:30]}...")
                content = self._extract_content_from_url(result['url'])
                result['snippet'] = content
                result['enhanced'] = True
            else:
                result['enhanced'] = False
            
            enhanced_results.append(result)
        
        # Добавляем необработанные результаты
        enhanced_results.extend(results[limit:])
        
        return enhanced_results

    def _fallback_extraction(self, soup, limit=5):
        """Резервный метод извлечения результатов"""
        results = []
        
        # Способ 1: извлечение заголовочных элементов
        for tag in ["h1", "h2", "h3", "h4"]:
            elements = soup.find_all(tag)
            for elem in elements:
                if len(results) >= limit:
                    break
                    
                title = self._clean_text(elem.get_text(strip=True))
                if self._is_valid_result(title, ""):
                    results.append({
                        "title": title,
                        "url": "",
                        "snippet": ""
                    })
        
        # Способ 2: извлечение текстовых блоков
        if not results:
            text_blocks = soup.get_text().split('\n')
            for block in text_blocks:
                if len(results) >= limit:
                    break
                    
                block = self._clean_text(block)
                if len(block) > 20 and len(block) < 150:
                    results.append({
                        "title": block,
                        "url": "",
                        "snippet": ""
                    })
        
        return results

    def run(self, parameters):
        # Безопасная обработка параметров
        if isinstance(parameters, dict):
            query = parameters.get("input", "")
        else:
            query = str(parameters) if parameters else ""

        # Проверка параметров
        if not query or not query.strip():
            return "Ошибка: ключевые слова поиска не могут быть пустыми"
        
        query = query.strip()
        self.last_query = query  # сохраняем запрос для подсказок
        limit = 5  # увеличенное число результатов
        
        # URL-кодирование параметров запроса
        encoded_query = quote_plus(query)
        url = f"https://duckduckgo.com/html/?q={encoded_query}"
        
        # Более реалистичный User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Определяем, содержит ли запрос иероглифы CJK
        is_cjk = any('\u4e00' <= char <= '\u9fff' for char in query)
        
        # Для CJK-запросов сразу используем Searx, пропуская DuckDuckGo (избегаем проблемы с кодом 202)
        if is_cjk:
            print(f"🌐 Обнаружен CJK-запрос, используем мультипоисковую стратегию...")
            searx_results, searx_success = self._search_searx(query, limit)
            
            if searx_success and searx_results:
                results = searx_results
                search_engine = "Searx мультипоиск"
                print(f"✅ CJK-поиск успешен, найдено {len(results)} результатов")
            else:
                # Если Searx не удался — поисковые подсказки
                print("⚠️ Все поисковые системы недоступны, предлагаем варианты поиска")
                results = self._get_search_suggestions(query)
                search_engine = "Поисковые подсказки"
        else:
            # Для латиницы: сначала DuckDuckGo, при неудаче — Searx
            max_retries = 2  # меньше повторов, быстрее переключение на Searx
            duckduckgo_success = False
            
            for attempt in range(max_retries):
                try:
                    print(f"🔍 Пробуем DuckDuckGo: {query} (попытка {attempt + 1}/{max_retries})")
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    # DuckDuckGo часто возвращает 202 — сразу переключаемся
                    if response.status_code == 202:
                        print("⚠️ DuckDuckGo вернул 202 (нужен JavaScript), переключаемся на Searx...")
                        break
                    
                    if response.status_code != 200:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        break
                    
                    # Проверка содержимого ответа
                    if len(response.text) < 1000:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        break
                    
                    soup = BeautifulSoup(response.text, "html.parser")
                    results = self._extract_duckduckgo_results(soup, limit)
                    
                    if results and len(results) > 0:
                        duckduckgo_success = True
                        search_engine = "DuckDuckGo"
                        print(f"✅ DuckDuckGo: поиск успешен, найдено {len(results)} результатов")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Попытка DuckDuckGo не удалась: {str(e)[:50]}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    break
            
            # Если DuckDuckGo не удался — Searx
            if not duckduckgo_success:
                print("🌐 DuckDuckGo недоступен, переключаемся на Searx...")
                searx_results, searx_success = self._search_searx(query, limit)
                
                if searx_success and searx_results:
                    results = searx_results
                    search_engine = "Searx мультипоиск"
                    print(f"✅ Searx: поиск успешен, найдено {len(results)} результатов")
                else:
                    print("⚠️ Все поисковые системы недоступны, предлагаем варианты поиска")
                    results = self._get_search_suggestions(query)
                    search_engine = "Поисковые подсказки"
        
        # Улучшение результатов (извлечение превью контента)
        if results:
            print("🚀 Улучшаем результаты, извлекаем превью контента...")
            enhanced_results = self._enhance_search_results(results, limit=3)
            results = enhanced_results
        
        # Форматирование вывода
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                result_text = f"{i}. {result['title']}"
                
                if result['url']:
                    result_text += f"\n   🔗 {result['url']}"
                
                if result['snippet']:
                    # Для улучшенных результатов показываем превью контента
                    if result.get('enhanced'):
                        result_text += f"\n   📄 Превью: {result['snippet']}"
                    else:
                        result_text += f"\n   📝 {result['snippet']}"
                
                formatted_results.append(result_text)
            
            return "\n\n".join(formatted_results)
        else:
            return f"Результаты по запросу «{query}» не найдены. Попробуйте другие ключевые слова."
        
    def _get_search_suggestions(self, query):
        """Быстро предоставляет поисковые подсказки"""
        return [
            {
                'title': f'Поиск в Google: {query}',
                'url': f'https://www.google.com/search?q={query}',
                'snippet': 'Поисковая система Google',
                'source': 'Google'
            },
            {
                'title': f'Поиск в Bing: {query}',
                'url': f'https://www.bing.com/search?q={query}',
                'snippet': 'Поисковая система Bing',
                'source': 'Bing'
            }
        ]

        return "Поиск не удался после нескольких попыток. Попробуйте позже."
