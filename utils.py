import requests
from collections import Counter
import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from sqlalchemy import desc
from datetime import datetime, timezone, timedelta
from orm_sqlite import Region, Vacancy, Schedule, Skill, search_vacancy, vacancies_skills, engine  # Импорт всех классов базы

# Создаем сессию
Session = sessionmaker(bind = engine)

def get_last_5_queries():
    # Выполняем запрос к таблицам с объединением
    session = Session()
   
    results = (
        session.query(
            Region.name.label('city'),
            Vacancy.name.label('vacancy_name'),
            Schedule.name.label('schedule_name'),
            search_vacancy.c.query_date,
            Skill.name.label('skill_name')
        )
        .join(search_vacancy, Region.id == search_vacancy.c.region_id)
        .join(Vacancy, Vacancy.id == search_vacancy.c.vacancy_id)
        .join(Schedule, Schedule.id == search_vacancy.c.schedule_id)
        .outerjoin(vacancies_skills, Vacancy.id == vacancies_skills.c.vacancy_id)
        .outerjoin(Skill, Skill.id == vacancies_skills.c.skill_id)
        .order_by(desc(search_vacancy.c.query_date))
        .limit(5)
        .all()
    )

    # Преобразуем результаты в удобный формат
    data = {}
    for row in results:
        query_date = row.query_date
        if query_date not in data:
            data[query_date] = {
                "city": row.city,
                "vacancy_name": row.vacancy_name,
                "schedule_name": row.schedule_name,
                "skills": []
            }
        if row.skill_name:
            data[query_date]["skills"].append(row.skill_name)

    # Возвращаем данные в формате списка
    return [
        {
            "city": value["city"],
            "vacancy_name": value["vacancy_name"],
            "schedule_name": value["schedule_name"],
            "query_date": key,
            "skills": value["skills"]
        }
        for key, value in sorted(data.items(), key=lambda x: x[0], reverse=True)
    ]


# Московское фиксированное время UTC+3
moscow_fixed_tz = timezone(timedelta(hours=3))

def save_search_to_db(region_name, name, schedule, skills):
    # Создаём новую сессию для данной операции
    session = Session()
    
    # Приводим текстовые данные к нижнему регистру
    region_name = region_name.lower()
    name = name.lower()
    schedule = schedule.lower()

    try:
        # Работа с таблицей Region
        region = session.query(Region).filter(Region.name.ilike(region_name)).first()
        if not region:
            region = Region(name=region_name)
            session.add(region)
            session.flush()  # Сохраняем временно, чтобы получить id

        # Работа с таблицей Vacancy
        vacancy = session.query(Vacancy).filter(Vacancy.name.ilike(name)).first()
        if not vacancy:
            vacancy = Vacancy(name=name)
            session.add(vacancy)
            session.flush()

        # Работа с таблицей Schedule
        schedule_record = session.query(Schedule).filter(Schedule.name.ilike(schedule)).first()
        if not schedule_record:
            schedule_record = Schedule(name=schedule)
            session.add(schedule_record)
            session.flush()

        # Сохранение данных в search_vacancy
        search_entry = search_vacancy.insert().values(
            region_id=region.id,
            vacancy_id=vacancy.id,
            schedule_id=schedule_record.id,
            query_date=datetime.now(moscow_fixed_tz)
        )
        session.execute(search_entry)

        # Сохранение навыков и связи через vacancy_skill
        for skill_name, skill_percent in skills.items():
            skill_name = skill_name.lower()

            # Проверяем, существует ли навык
            skill = session.query(Skill).filter(Skill.name.ilike(skill_name)).first()
            if not skill:
                skill = Skill(name=skill_name)
                session.add(skill)
                session.flush()

            # Добавляем связь в vacancies_skills
            skill_link = vacancies_skills.insert().values(
                vacancy_id=vacancy.id,
                skill_id=skill.id
            )
            session.execute(skill_link)

        # Сохраняем изменения
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

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

