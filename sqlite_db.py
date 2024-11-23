import sqlite3

DATABASE = 'hh_sqlite.db'  # Имя файла базы данных

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Для доступа к данным как к словарю
    return conn

def save_search_to_db(region_name, name, schedule, skills):
    conn = get_db_connection()
    try:
        # Приводим текстовые данные к нижнему регистру
        region_name = region_name.lower()
        name = name.lower()
        schedule = schedule.lower()

        # Сохранение города, если он еще не добавлен
        cursor = conn.execute('SELECT id FROM cities WHERE LOWER(name_city) = ?', (region_name,))
        city = cursor.fetchone()
        if not city:
            conn.execute('INSERT INTO cities (name_city) VALUES (?)', (region_name,))
            city_id = conn.execute('SELECT id FROM cities WHERE LOWER(name_city) = ?', (region_name,)).fetchone()['id']
        else:
            city_id = city['id']

        # Сохранение вакансии, если она еще не добавлена
        cursor = conn.execute('SELECT id FROM vacancies WHERE LOWER(name_vacancy) = ?', (name,))
        vacancy = cursor.fetchone()
        if not vacancy:
            conn.execute('INSERT INTO vacancies (name_vacancy) VALUES (?)', (name,))
            vacancy_id = conn.execute('SELECT id FROM vacancies WHERE LOWER(name_vacancy) = ?', (name,)).fetchone()['id']
        else:
            vacancy_id = vacancy['id']

        # Сохранение графика
        cursor = conn.execute('SELECT id FROM schedules WHERE LOWER(type_schedule) = ?', (schedule,))
        schedule_record = cursor.fetchone()
        if schedule_record:
            schedule_id = schedule_record['id']
        else:
            conn.execute('INSERT INTO schedules (type_schedule) VALUES (?)', (schedule,))
            schedule_id = conn.execute('SELECT id FROM schedules WHERE LOWER(type_schedule) = ?', (schedule,)).fetchone()['id']

        # Сохранение данных в таблице search_vacancy
        conn.execute('INSERT INTO search_vacancy (city_id, vacancy_id, schedule_id, query_date) VALUES (?, ?, ?, DATE("now"))',
                     (city_id, vacancy_id, schedule_id))
        search_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Сохранение топ-10 навыков
        for skill_name, skill_percent in skills.items():
            # Приведение названия навыка к нижнему регистру
            skill_name = skill_name.lower()

            # Проверяем, существует ли навык
            cursor = conn.execute('SELECT id FROM skills WHERE LOWER(name_skill) = ?', (skill_name,))
            skill = cursor.fetchone()
            if not skill:
                conn.execute('INSERT INTO skills (name_skill) VALUES (?)', (skill_name,))
                skill_id = conn.execute('SELECT id FROM skills WHERE LOWER(name_skill) = ?', (skill_name,)).fetchone()['id']
            else:
                skill_id = skill['id']

            # Сохраняем связь в таблице vacancy_skills
            conn.execute('INSERT INTO vacancy_skills (vacancy_id, skill_id) VALUES (?, ?)', (vacancy_id, skill_id))

        conn.commit()  # Сохраняем изменения
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
