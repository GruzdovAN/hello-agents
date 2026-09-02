#!/usr/bin/env python3
# mx_moni — Замечательные навыки управления комбинациями симуляций.

import os
import sys
import json
import re
import requests
from typing import Dict, Any, Optional, Tuple

#Загрузить переменные среды
MX_APIKEY = os.environ.get('MX_APIKEY')
MX_API_URL = os.environ.get('MX_API_URL', 'https://mkapi2.dfcfs.com/finskillshub')
OUTPUT_DIR = '/root/.openclaw/workspace/mx_data/output'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def check_apikey() -> None:
    """检查API密钥是否配置"""
    if not MX_APIKEY:
print("Ошибка: переменная среды MX_APIKEY не настроена, сначала настройте ключ API")
        print("示例: export MX_APIKEY=your_api_key_here")
        sys.exit(1)

def make_request(endpoint: str, body: Dict[str, Any], output_prefix: str) -> None:
"""Отправьте POST-запрос и сохраните результат"""
    check_apikey()
    full_url = f"{MX_API_URL}{endpoint}"
    headers = {
        'apikey': MX_APIKEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(full_url, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        
        output_path = os.path.join(OUTPUT_DIR, f"{output_prefix}_raw.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
print(f"Запрос выполнен, результат сохранен в {output_path}")
        
#Распечатать сводку результатов
        if result.get('success') or str(result.get('code')) == '200':
print("\nРезультат операции: Успех")
            if 'message' in result:
                print(f"提示信息: {result['message']}")
            if 'data' in result and isinstance(result['data'], dict):
                data = result['data']
                if 'totalAssets' in data:
print(f"\nСредства на счете:")
                    print(f"  总资产: {data['totalAssets']:.2f} 元")
                    print(f"  可用资金: {data['availBalance']:.2f} 元")
                if 'orderId' in data:
print(f"\nДелегирование успешно:")
                    print(f"  委托编号: {data['orderId']}")
        else:
print(f"\nРезультат операции: не удалось")
print(f"Код ошибки: {result.get('code')}")
            print(f"错误信息: {result.get('message')}")
    except Exception as e:
print(f"Ошибка сетевого запроса: {str(e)}")
        sys.exit(1)

def parse_buy_sell(query: str) -> Tuple[Optional[str], Optional[float], Optional[int], bool]:
"""Разбор ордеров на покупку и продажу и возврат (код акции, цена, количество, рыночная цена или нет)"""
# Извлечь 6-значный биржевой код
    code_match = re.search(r'(\d{6})', query)
    if not code_match:
        return None, None, None, False
    stock_code = code_match.group(1)
    
# Сумма вывода (единица измерения: доля, должна быть кратна 100)
    quantity_match = re.search(r'(\d+)\s*(股|手)', query)
    quantity = None
    if quantity_match:
        qty = int(quantity_match.group(1))
if Quantity_match.group(2) == '手':
            qty = qty * 100
        quantity = qty
    
# Проверяем, сделан ли рыночный ордер
is_market = Any(слово в запросе для слова в ['рыночная цена', 'покупка по рыночной цене', 'продажа по рыночной цене', 'покупка по текущей цене', 'продажа по текущей цене'])
    
#Извлечь цену
Price_match = re.search(r'(\d+\.?\d*)\s*元', query), если не is_market, иначе Нет
    price = None
    if price_match and not is_market:
        price = float(price_match.group(1))
    elif not is_market and quantity:
        # 尝试找任意数字作为价格
        price_candidates = re.findall(r'\d+\.?\d*', query)
        for candidate in price_candidates:
if len(candidate) != 6: # Исключить коды акций
                price = float(candidate)
                break
    
    return stock_code, price, quantity, is_market

def parse_cancel(query: str) -> Tuple[Optional[str], Optional[str], bool]:
"""Разобрать команду отмены заказа и вернуть (номер заказа, код акции, отменить ли все заказы)"""
    if any(word in query for word in ['全部', '所有', '一键撤单']):
        return None, None, True
    
#Извлекаем номер заказа
    order_id_match = re.search(r'(\d{16,20})', query)
    order_id = order_id_match.group(1) if order_id_match else None
    
#Извлекаем биржевой код
    code_match = re.search(r'(\d{6})', query)
    stock_code = code_match.group(1) if code_match else None
    
    return order_id, stock_code, False

def main():
    if len(sys.argv) < 2:
print("Пожалуйста, предоставьте инструкции по эксплуатации, например:")
        print("  python mx_moni.py 我的持仓      # 查询持仓")
        print("  python mx_moni.py 我的资金      # 查询资金")
        print("  python mx_moni.py 我的委托      # 查询委托订单")
        print("  python mx_moni.py 买入 600519 价格 1700 数量 100 股")
        print("  python mx_moni.py 市价买入 600519 100 股")
        print("  python mx_moni.py 卖出 600519 价格 1750 数量 100 股")
        print("  python mx_moni.py 撤单 123456789012345678")
print("python mx_moni.py отмена заказа в один клик")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    output_prefix = f"mx_moni_{query.replace(' ', '_')}"
    
# Вызов различных интерфейсов на основе идентификации намерения
    if any(word in query for word in ['持仓', '我的持仓', '持仓情况']):
        make_request('/api/claw/mockTrading/positions', {'moneyUnit': 1}, output_prefix)
    elif any(word in query for word in ['资金', '我的资金', '账户余额', '资金情况']):
        make_request('/api/claw/mockTrading/balance', {'moneyUnit': 1}, output_prefix)
    elif any(word in query for word in ['委托', '我的委托', '订单', '委托记录']):
        make_request('/api/claw/mockTrading/orders', {'fltOrderDrt': 0, 'fltOrderStatus': 0}, output_prefix)
    elif any(word in query for word in ['买入', '买进', '建仓']):
        stock_code, price, quantity, is_market = parse_buy_sell(query)
        if not stock_code or not quantity:
            print("错误: 无法解析买入指令，请确保包含股票代码(6位)和数量(100的整数倍)")
            print("示例: python mx_moni.py 买入 600519 价格 1700 数量 100 股")
            print("示例: python mx_moni.py 市价买入 600519 100 股")
            sys.exit(1)
        if not is_market and price is None:
print("Ошибка: для лимитной покупки требуется цена или используйте рыночную покупку")
            sys.exit(1)
        if quantity % 100 != 0:
print("Ошибка: количество заказов должно быть целым кратным 100")
            sys.exit(1)
        
        body = {
            'type': 'buy',
            'stockCode': stock_code,
            'quantity': quantity,
            'useMarketPrice': is_market
        }
        if not is_market:
            body['price'] = price
        
        make_request('/api/claw/mockTrading/trade', body, output_prefix)
    elif any(word in query for word in ['卖出', '抛售', '减仓']):
        stock_code, price, quantity, is_market = parse_buy_sell(query)
        if not stock_code or not quantity:
            print("错误: 无法解析卖出指令，请确保包含股票代码(6位)和数量(100的整数倍)")
print("Пример: python mx_moni.py продать 600519 цена 1750 количество 100 акций")
            print("示例: python mx_moni.py 市价卖出 600519 100 股")
            sys.exit(1)
        if not is_market and price is None:
print("Ошибка: вам необходимо указать цену для продажи по лимитной цене или использовать рыночную цену для продажи")
            sys.exit(1)
        if quantity % 100 != 0:
print("Ошибка: количество заказов должно быть целым кратным 100")
            sys.exit(1)
        
        body = {
            'type': 'sell',
            'stockCode': stock_code,
            'quantity': quantity,
            'useMarketPrice': is_market
        }
        if not is_market:
            body['price'] = price
        
        make_request('/api/claw/mockTrading/trade', body, output_prefix)
    elif any(word in query for word in ['撤单', '撤销', '撤单']):
        order_id, stock_code, is_all = parse_cancel(query)
        if is_all:
            body = {'type': 'all'}
            make_request('/api/claw/mockTrading/cancel', body, output_prefix)
        else:
            if not order_id:
                print("错误: 请提供委托编号，或使用一键撤单撤销所有未成交委托")
                print("示例: python mx_moni.py 撤单 260854300000078983")
                print("示例: python mx_moni.py 一键撤单")
                sys.exit(1)
            body = {
                'type': 'order',
                'orderId': order_id
            }
            if stock_code:
                body['stockCode'] = stock_code
            make_request('/api/claw/mockTrading/cancel', body, output_prefix)
    else:
print("Невозможно распознать намерение, используйте одно из следующих действий:")
print("Запрос позиции: Моя позиция/Позиция запроса")
print("Запрос фонда: Мои средства / Запрос средств")
print("Запрос делегирования: мое делегирование/запрос делегирования")
        print("  买入操作: 买入 [股票代码] [价格] [数量] 股 / 市价买入 [股票代码] [数量] 股")
        print("  卖出操作: 卖出 [股票代码] [价格] [数量] 股 / 市价卖出 [股票代码] [数量] 股")
print("Операция отмены: Отменить [номер заказа] / Отменить заказ одним щелчком мыши")
        sys.exit(1)

if __name__ == '__main__':
    main()
