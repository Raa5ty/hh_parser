from flask import Flask, render_template, request, abort
from collections import Counter
from utils import find_area_id, get_skills, areas
import logging

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        try:
            region_name = request.form['region_name']
            name = request.form['name']
            schedule = request.form['schedule']
            
            logging.debug(f"Получены данные формы: регион={region_name}, название={name}, график={schedule}")
            
            area = find_area_id(region_name, areas)
            
            params = {
                'text': name,
                'area': area,
                'schedule': schedule
            }
            
            skills, total_vacancies = get_skills(params)
            
            logging.debug(f"Получены результаты: навыки={skills}, всего вакансий={total_vacancies}")
            
            return render_template('results.html', 
                                   region_name=region_name, 
                                   name=name, 
                                   schedule=schedule, 
                                   skills=skills, 
                                   total_vacancies=total_vacancies)
        except Exception as e:
            logging.error(f"Произошла ошибка: {str(e)}")
            abort(500)
    return render_template('form.html')

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
    # # Очистка навыков от лишних символов
    # cleaned_skills = [re.sub(r'[^\w\s]', '', skill).strip() for skill in all_skills]

    # # Подсчет частоты навыков
    # skill_counts = Counter(cleaned_skills)

    # print("\nТоп-20 наиболее востребованных навыков:")

    # result = {
    #     "Название вакансии": name,
    #     "Регион": region_name,
    #     "Тип занятости": schedule,
    #     "Найдено вакансий": total_vacancies,
    #     "Навыки": {}
    # }
    # for skill, count in skill_counts.most_common(20):
    #     percentage = (count / total_vacancies) * 100
    #     capitalized_skill = skill.capitalize()
    #     result["Навыки"][capitalized_skill] = f"{percentage:.1f}%"
    #     print(f"{capitalized_skill}: {percentage:.1f}%")

    # # Сохранение результата в JSON файл
    # with open('skill_results.json', 'w', encoding='utf-8') as f:
    #     json.dump(result, f, ensure_ascii=False, indent=4)

    # print("\nРезультаты сохранены в файл 'skill_results.json'")

