import streamlit as st
import requests
import json

# Функция сбора данных
def get_bitcoin_price():
    try:
        # Получить данные о ценах на биткойны
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true')
        data = response.json()
        # Получите текущие цены и изменения в течение 24 часов.
        current_price = data['bitcoin']['usd']
        price_change_percentage = data['bitcoin']['usd_24h_change']

        return current_price, price_change_percentage
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None, None

# Инициализируйте приложение Streamlit
st.title('Текущая цена биткойнов')
st.subheader('Получите самую свежую информацию о ценах на биткойны и их 24-часовой тренд цен.')

# Добавить кнопку обновления
if st.button('обновить цену'):
    st.experimental_rerun()

# показать статус загрузки
with st.spinner('загрузка...'):
    current_price, price_change_percentage = get_bitcoin_price()

# отображать данные
if current_price is not None:
    st.metric(label="Текущая цена биткойнов (долл. США)", value=f"${current_price}")

    if price_change_percentage is not None:
        st.metric(label="Изменение за 24 часа (%)", value=f"{price_change_percentage:.2f}%")
else:
    st.error("Не удалось получить данные. Повторите попытку позже.")