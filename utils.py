import requests
from collections import Counter
import re

# Получаем список всех регионов
areas = requests.get('https://api.hh.ru/areas').json()

# Функция для поиска ID региона по названию
def find_area_id(name, areas):
    def search(items):
        for item in items:
            if item['name'].lower() == name.lower():
                return item['id']
            if 'areas' in item and item['areas']:
                result = search(item['areas'])
                if result:
                    return result
        return None

    result = search(areas)
    if result:
        return result
    else:
        raise ValueError(f"Регион '{name}' не найден")

# Получаем список всех вакансий
url_vacancies = 'https://api.hh.ru/vacancies'

# Функция поиска скиллов в отобранных вакансиях
def get_skills(params):
    all_skills = []
    page = 0
    pages_total = 1
    total_vacancies = 0
    
    while page < pages_total:
        params['page'] = page
        result = requests.get(url_vacancies, params=params).json()
        
        if page == 0:
            pages_total = min(result['pages'], 20)  # Ограничим 20 страницами
            total_vacancies = result['found']
        
        items = result['items']

        for i, item in enumerate(items):
            vacancy_url = item['url']
            vacancy_data = requests.get(vacancy_url).json()
            
            if 'key_skills' in vacancy_data and vacancy_data['key_skills']:
                skills = [skill['name'].lower() for skill in vacancy_data['key_skills']]
                all_skills.extend(skills)
            
            progress = (page * len(items) + i + 1) / (pages_total * len(items)) * 100
            print(f"\rПрогресс обработки запроса: {progress:.1f}%", end="")
        
        page += 1

    # Очистка навыков от лишних символов
    cleaned_skills = [re.sub(r'[^\w\s]', '', skill).strip() for skill in all_skills]

    # Подсчет частоты навыков
    skill_counts = Counter(cleaned_skills)
    skill_percentages = {skill: round((count / total_vacancies) * 100, 2) for skill, count in skill_counts.items()}
    
    return skill_percentages, total_vacancies




