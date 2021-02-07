# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, url_for
import requests
from bs4 import BeautifulSoup
import json, sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    # отображение html файла на главной странице
    return render_template("index.html")


@app.route('/specialty', methods=['GET', 'POST'])
def specialty():
    # подключаюсь к БД
    con = sqlite3.connect("static/db/universities.db")
    cur = con.cursor()
    
    # получение данных из ajax запроса
    id1 = request.form['id']
    
    # выполняю запрос и получаю данные из БД
    universities = cur.execute("""SELECT u.* FROM universities_specialties us
                INNER JOIN universities u ON u.id = us.university_id
                WHERE us.specialty_id = ?""", (id1, )).fetchall() 
    
    specialty = cur.execute("""SELECT name, code
                FROM specialties WHERE id = ?""", (id1, )).fetchone()  
    
    # превращение полученных данных в словарь для удобства отправки
    specialty = {['name', 'code'][i]: name
                  for i, name in enumerate(specialty)}
    
    universities_li = []
    for i in universities: 
        univs = {['name', 'city', 'image', 'placeInRussianTop', 
                  'description'][i]: name 
                    for i, name in enumerate(i[1:])} 
        budget = cur.execute("""SELECT budgetary_places
                    FROM universities_specialties 
                    WHERE specialty_id = ?""", (i[0], )).fetchone()  
        univs['budget'] = budget[0]
        universities_li.append(univs)
        
    # слияние словарей
    specialty['universities'] = universities_li
        
    # возврат полученных данных в json формате
    return json.dumps(specialty)


@app.route('/specialties', methods=['GET', 'POST'])
def specialties():
    # подключение к БД
    con = sqlite3.connect("static/db/universities.db")
    cur = con.cursor()
    
    # выполняю запрос и получаю данные из БД
    universities = cur.execute("""SELECT name, code, description
                FROM specialties""").fetchall()  
    
    # превращение полученных данных в словарь для удобства отправки
    specialties_li = []
    for i in universities: 
        specials = {['name', 'code', 'description'][i]: name 
                    for i, name in enumerate(i)} 
        specialties_li.append(specials)
        
    # возврат полученных данных в json формате
    return json.dumps(specialties_li)


@app.route('/universities', methods=['GET', 'POST'])
def universities():
    # подключение к БД
    con = sqlite3.connect("static/db/universities.db")
    cur = con.cursor()
    
    # выполняю запрос и получаю данные из БД
    universities = cur.execute("""SELECT id, name, city, image, 
                placeInRussianTop, description FROM universities""").fetchall()  
    
    # превращение полученных данных в словарь для удобства отправки
    universities_li = []
    for i in universities: 
        univs = {['id', 'name', 'city', 'image', 'placeInRussianTop', 
                  'description'][i]: name 
                    for i, name in enumerate(i)} 
        rating = cur.execute("""SELECT AVG(rating), COUNT(rating) FROM reviews 
                    WHERE university_id = ?""", (i[0], )).fetchone() 
        rating = {['avg', 'count'][i]: name
                  for i, name in enumerate(rating)}  
        univs.update(rating)
        universities_li.append(univs)
        
    # возврат полученных данных в json формате
    return json.dumps(universities_li)
    
    

@app.route('/university', methods=['GET', 'POST'])
def university():
    # подключение к БД
    con = sqlite3.connect("static/db/universities.db")
    cur = con.cursor()
    
    # получение данных из ajax запроса
    id1 = request.form['id']
    
    # выполнение запроса и получение данных из БД
    university = cur.execute("""SELECT name, city, image, placeInRussianTop, 
                description FROM universities WHERE id = ?""", (id1, )).fetchone() 
    
    specialties = cur.execute("""SELECT s.* 
                FROM universities_specialties us
                INNER JOIN specialties s ON s.id = us.specialty_id
                WHERE us.university_id = ?""", (id1, )).fetchall() 
    
    rating = cur.execute("""SELECT AVG(rating), COUNT(rating) FROM reviews 
                WHERE university_id = ?""", 
                         (id1, )).fetchone()     
    
    ratings = cur.execute("""SELECT user_name, text, rating FROM reviews 
                WHERE university_id = ?""", (id1, )).fetchall()     
    
    # превращение полученных данных в словарь для удобства отправки
    university = {['name', 'city', 'image', 'placeInRussianTop', 
                   'description'][i]: name
                  for i, name in enumerate(university)}
    
    specials_li = []
    for i in specialties: 
        specials = {['code', 'name', 'description'][i]: name 
                    for i, name in enumerate(i[1:])} 
        budget = cur.execute("""SELECT budgetary_places
                    FROM universities_specialties 
                    WHERE specialty_id = ?""", (i[0], )).fetchone()  
        specials['budget'] = budget[0]
        specials_li.append(specials)
    
    rating = {['avg', 'count'][i]: name
              for i, name in enumerate(rating)}  
    
    ratings_li = []
    for i in ratings: 
        rats = {['user_name', 'text', 'rating'][i]: name 
                    for i, name in enumerate(i)} 
        ratings_li.append(rats)    
    
    # парсер последних 5 новостей
    url, title, text, date = cur.execute("""SELECT url, title, text, date FROM news 
            WHERE university_id = ?""", (id1, )).fetchone()  

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    titles = []
    texts = []
    dates = []
    
    for link in soup.find_all(title.split()[0], class_ =  title.split()[1])[:5]: 
        titles.append(link.text.strip())
        
        
    for link in soup.find_all(date.split()[0], class_ =  date.split()[1])[:5]: 
        dates.append(' '.join(link.text.strip().split()))
        
    if text != '':
        for link in soup.find_all(text.split()[0], class_ =  text.split()[1])[:5]: 
            texts.append(link.text.strip())
    
    # превращение полученных данных в словарь для удобства отправки
    news_li = []
    for i in range(5):
        dict1 = {}
        dict1['title'] = titles[i]
        dict1['text'] = texts[i]
        dict1['date'] = dates[i]
        news_li.append(dict1)
    
    # слияние словарей и списков
    university.update(rating)
    university['specialties'] = specials_li
    university['ratings'] = ratings_li
    university['news'] = news_li
        
    # возврат полученных данных в json формате
    return json.dumps(university)


if __name__ == '__main__':
    app.run(debug=True)