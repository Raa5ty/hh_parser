from sqlalchemy import Column, Integer, String, DateTime, create_engine, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base

# Создаём движок базы данных
engine = create_engine('sqlite:///orm_sqlite.db')

# Создаём базовый класс для таблиц
Base = declarative_base()

# Создаём класс для таблицы region
class Region(Base):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return f"<Region(id={self.id}, name={self.name})>"
    
class Vacancy(Base):
    __tablename__ = 'vacancies'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"<Vacancy(id={self.id}, name={self.name})>"

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"<Schedule(id={self.id}, name={self.name})>"       
    
class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"<Skill(id={self.id}, name={self.name})>"
    
vacancies_skills = Table('vacancies_skills', Base.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
                     Column('skill_id', Integer, ForeignKey('skills.id'))
                     )

search_vacancy = Table('search_vacancy', Base.metadata,
                     Column('id', Integer, primary_key=True),
                     Column('region_id', Integer, ForeignKey('regions.id')),
                     Column('vacancy_id', Integer, ForeignKey('vacancies.id')),
                     Column('schedule_id', Integer, ForeignKey('schedules.id')),
                     Column('query_date', DateTime)
                     )


# Создание таблицы (выполняется один раз при запуске)
Base.metadata.create_all(engine)