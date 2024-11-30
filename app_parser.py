from flask import Flask, render_template, request, redirect, url_for, session
from collections import Counter
from utils import find_area_id, get_skills, areas, save_search_to_db, get_last_5_queries
import logging
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)  # Для работы с session генерирует случайный ключ длиной 24 байта

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Показываем индикатор загрузки
        loading = True
        try:
            region_name = request.form['region_name']
            name = request.form['name']
            schedule_value = request.form['schedule']  # Сохраняем значение графика

            # Сопоставляем значения графиков с отображаемыми названиями
            schedule_names = {
                'fullDay': 'Полный день',
                'shift': 'Сменный график',
                'remote': 'Удалённая работа',
                'flexible': 'Гибкий график'
            }
            schedule_display = schedule_names.get(schedule_value, 'Не указан')

            
            logging.debug(f"Получены данные формы: регион={region_name}, название={name}, график={schedule_display}")
            
            # Получение навыков и общего количества вакансий
            skills, total_vacancies = get_skills({
                'text': name,
                'area': find_area_id(region_name, areas),
                'schedule': schedule_value
            })
            
            logging.debug(f"Получены результаты: навыки={skills}, всего вакансий={total_vacancies}")

            # Сортируем навыки по убыванию процента и сохраняем топ-10 в session
            sorted_skills = dict(sorted(skills.items(), key=lambda item: item[1], reverse=True)[:10])

            # Сохранение данных в базу данных
            save_search_to_db(region_name, name, schedule_display, sorted_skills)

            # Сохраняем данные в session для передачи на /results
            session['region_name'] = region_name
            session['name'] = name
            session['schedule'] = schedule_display
            session['skills'] = sorted_skills
            session['total_vacancies'] = total_vacancies
          
            return redirect(url_for('results'))
        
        except Exception as e:
            logging.error(f"Произошла ошибка: {str(e)}")
            return render_template('error.html', error=str(e)), 500  # добавлено отображение сообщения об ошибке
    return render_template('form.html')

# страница результатов
@app.route('/results')
def results():
    # Получаем данные из session
    region_name = session.get('region_name')
    name = session.get('name')
    schedule_display = session.get('schedule', 'Не указан')
    skills = session.get('skills', {})
    total_vacancies = session.get('total_vacancies', 0)

    # Сортируем навыки по убыванию процента уже на этапе подготовки данных
    sorted_skills = dict(sorted(skills.items(), key=lambda item: item[1], reverse=True))

    return render_template('results.html', 
                           region_name=region_name, 
                           name=name, 
                           schedule=schedule_display, 
                           skills=sorted_skills, 
                           total_vacancies=total_vacancies)

# страница истории запросов
@app.route('/history')
def history():
    # Получаем данные из базы данных
    queries = get_last_5_queries()
    return render_template('history.html', queries=queries)

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True)