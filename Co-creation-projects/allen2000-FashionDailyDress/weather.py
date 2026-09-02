import requests
import os
from dotenv import load_dotenv

load_dotenv()

class Weather:
    """Класс запроса погоды, инкапсулирующий API OpenWeatherMap"""
    
    def __init__(self, api_key=None, unit='metric'):
        """
        Инициализация класса Weather
        :param api_key: ключ API OpenWeatherMap, по умолчанию из переменной окружения OPENWEATHER_API_KEY
        :param unit: единица температуры (metric=Цельсий, imperial=Фаренгейт)
        """
        self.api_key = api_key or os.environ.get("OPENWEATHER_API_KEY")
        self.unit = unit
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

        # Если ключ API не задан — демонстрационный режим
        self.demo_mode = not self.api_key
        if self.demo_mode:
            print("⚠️  Предупреждение: ключ API не задан, используется демонстрационный режим")
            print("   Установите переменную окружения OPENWEATHER_API_KEY для получения реальных данных")
    
    def get_weather(self, city_name):
        """
        Запрос погоды для указанного города
        :param city_name: название города (на английском)
        :return: отформатированная строка с погодной информацией
        """
        # В демонстрационном режиме — имитационные данные
        if self.demo_mode:
            return self._get_demo_weather()
        
        params = {
            "q": city_name,
            "appid": self.api_key,
            "units": self.unit
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()

            if response.status_code == 200:
                return self._format_weather_data(data)
            else:
                return f"Ошибка {data['cod']}: {data['message']}"

        except Exception as e:
            return f"Запрос не выполнен: {str(e)}"
    
    def get_weather_details(self, city_name):
        """
        Получить подробные погодные данные (в формате словаря)
        :param city_name: название города (на английском)
        :return: словарь с подробными погодными данными
        """
        # В демонстрационном режиме — имитационные данные
        if self.demo_mode:
            return self._get_demo_weather()
        
        params = {
            "q": city_name,
            "appid": self.api_key,
            "units": self.unit
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()

            if response.status_code == 200:
                return self._parse_weather_data(data)
            else:
                return {"error": f"Ошибка {data['cod']}: {data['message']}"}

        except Exception as e:
            return {"error": f"Запрос не выполнен: {str(e)}"}

    def _get_demo_weather(self):
        return {
            "city": 'shanghai',
            "temperature": 25,
            "temperature_unit": "°C",
            "description": "ясно",
            "humidity": 60,
            "wind_speed": 10,
            "wind_unit": "m/s"
        }
    def _parse_weather_data(self, data):
        """
        Разбор погодных данных в формат словаря
        :param data: исходные данные от API
        :return: словарь с разобранными погодными данными
        """
        weather_desc = data['weather'][0]['description'].title()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        city = data['name']
        
        return {
            "city": city,
            "temperature": temp,
            "temperature_unit": "°C" if self.unit == 'metric' else "°F",
            "description": weather_desc,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_unit": "m/s"
        }
    
    def _format_weather_data(self, data):
        """
        Форматирование погодных данных в строку
        :param data: исходные данные от API
        :return: отформатированная строка с погодной информацией
        """
        weather_data = self._parse_weather_data(data)
        
        return (
            f"🏙️ Город: {weather_data['city']}\n"
            f"🌡️ Температура: {weather_data['temperature']}{weather_data['temperature_unit']}\n"
            f"📝 Погода: {weather_data['description']}\n"
            f"💧 Влажность: {weather_data['humidity']}%\n"
            f"🌬️ Скорость ветра: {weather_data['wind_speed']} {weather_data['wind_unit']}"
        )
    
    def set_unit(self, unit):
        """
        Установка единицы температуры
        :param unit: единица температуры (metric=Цельсий, imperial=Фаренгейт)
        """
        if unit not in ['metric', 'imperial']:
            raise ValueError("Единица должна быть 'metric' или 'imperial'")
        self.unit = unit
    
    def set_api_key(self, api_key):
        """
        Установка ключа API
        :param api_key: новый ключ API
        """
        self.api_key = api_key


def get_weather(city_name, api_key=os.environ.get("OPENWEATHER_API_KEY"), unit='metric'):
    """
    Функция обратной совместимости на основе класса Weather
    :param city_name: название города (на английском)
    :param api_key: ваш ключ API OpenWeatherMap
    :param unit: единица температуры (metric=Цельсий, imperial=Фаренгейт)
    :return: отформатированная погодная информация
    """
    weather = Weather(api_key=api_key, unit=unit)
    return weather.get_weather(city_name)


# Пример использования
if __name__ == "__main__":
    weather = Weather()
    weather_info = weather.get_weather("harbin")
    print(weather_info)
