from sqlalchemy.orm import sessionmaker
from datetime import datetime
from orm_sqlite import Region, Vacancy, Schedule, Skill, search_vacancy, vacancies_skills, engine  # Импорт всех классов базы

# Создаем сессию
Session = sessionmaker(bind = engine)

def save_search_to_db(region_name, name, schedule, skills):
    # Создаём новую сессию для данной операции
    session = Session()
    try:
        # Приводим текстовые данные к нижнему регистру
        region_name = region_name.lower()
        name = name.lower()
        schedule = schedule.lower()

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
            query_date=datetime.utcnow()
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
