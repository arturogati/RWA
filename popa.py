import requests

# URL API Checko с вашим ключом и ИНН
url = "https://api.checko.ru/v2/finances"
params = {
    "key": "yCEWUepinagwBCn3",  # Ваш API-ключ
    "inn": "5009051111"         # ИНН компании
}

try:
    # Отправляем GET-запрос
    response = requests.get(url, params=params)
    
    # Проверяем статус ответа
    if response.status_code == 200:
        # Получаем JSON-ответ
        data = response.json()
        print(data)  # Выводим JSON
    else:
        print(f"Ошибка: {response.status_code}")
        print(response.text)  # Выводим текст ошибки

except requests.exceptions.RequestException as e:
    print(f"Ошибка при выполнении запроса: {e}")