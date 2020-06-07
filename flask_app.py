from flask import Flask, render_template, request, redirect, url_for
from matplotlib import pyplot
from pymorphy2 import MorphAnalyzer
from nltk.corpus import stopwords
from functions import search, get_dicts
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import psutil
import base64
import io
import sys
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl

from nltk.tokenize import word_tokenize
from emoji.unicode_codes import UNICODE_EMOJI
from collections import Counter
sys.path.append(r"C:\Users\Veronuka\AppData\Roaming\Python\Python38\site-packages")
morph = MorphAnalyzer()
sw = stopwords.words('russian')

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vk_info.db'
db = SQLAlchemy(app)


class Authors(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    sex = db.Column(db.Text)
    bdate = db.Column(db.Text)
    day = db.Column(db.Integer)
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)
    city = db.Column(db.Text)
    faculty = db.Column(db.Text)
    books = db.Column(db.Text)
    interests = db.Column(db.Text)
    home_town = db.Column(db.Text)
    career = db.Column(db.Text)


class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    author_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    lem_text = db.Column(db.Text)
    likes = db.Column(db.Integer)
    date_time = db.Column(db.Text)
    weekday = db.Column(db.Text)
    wall_owner = db.Column(db.Integer)


class Posts(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    lem_text = db.Column(db.Text)
    likes = db.Column(db.Integer)
    date_time = db.Column(db.Text)
    weekday = db.Column(db.Text)
    wall_owner = db.Column(db.Integer)


@app.route('/')
def index():
    return render_template(
        'main.html')


@app.route('/form', methods=['GET'])
def answer_process():
    if not request.args:
        return redirect(url_for('index'))
    user_type = request.args.get('user_type')
    id_type = request.args.get('id_type')
    some_id = request.args.get('some_id')
    if user_type and id_type and some_id:
        owner_list = []
        owner_stats = db.session.query(Posts.wall_owner).all()
        w = 'owner_stats'
        for item in owner_stats:
            owner_list.append(str(item[0]))
        if str(some_id) in owner_list:
            w = 'Информация об этом пользователе уже есть.'
            return render_template('search.html', owner_id=some_id, w=w)
        else:
            all_comments, all_posts, all_authors = search(user_type, id_type, some_id)
            com_df = pd.DataFrame(all_comments)
            post_df = pd.DataFrame(all_posts)
            auth_df = pd.DataFrame(all_authors)
            # posts
            for index, row in post_df.iterrows():
                id = row['id']
                author_id = row['user_id']
                text = row['text']
                lem_text = row['lem_text']
                likes = row['likes']
                date_time = row['date_time']
                weekday = row['weekday']
                wall_owner = row['wall_owner']
                post = Posts(
                    id=id,
                    author_id=author_id,
                    text=text,
                    lem_text=lem_text,
                    likes=likes,
                    date_time=date_time,
                    weekday=weekday,
                    wall_owner=wall_owner
                )
                db.session.add(post)
                db.session.commit()
                db.session.refresh(post)
            # comments
            for index, row in com_df.iterrows():
                id = row['id']
                post_id = row['post_id']
                author_id = row['author_id']
                text = row['text']
                lem_text = row['lem_text']
                likes = row['likes']
                date_time = row['date_time']
                weekday = row['weekday']
                wall_owner = row['wall_owner']
                comment = Comments(
                    id=id,
                    post_id=post_id,
                    author_id=author_id,
                    text=text,
                    lem_text=lem_text,
                    likes=likes,
                    date_time=date_time,
                    weekday=weekday,
                    wall_owner=wall_owner
                )
                db.session.add(comment)
                db.session.commit()
                db.session.refresh(comment)
            # authors
            author_base = []
            author_stats = db.session.query(Authors.id).all()
            for item in author_stats:
                author_base.append(item[0])
            for index, row in auth_df.iterrows():
                if row['id'] not in author_base:
                    id = row['id']
                    sex = row['sex']
                    bdate = row['bdate']
                    day = row['day']
                    month = row['month']
                    year = row['year']
                    city = row['city']
                    faculty = row['faculty']
                    books = row['books']
                    interests = row['interests']
                    home_town = row['home_town']
                    career = row['career']
                    author = Authors(
                        id=id,
                        sex=sex,
                        bdate=bdate,
                        day=day,
                        month=month,
                        year=year,
                        city=city,
                        faculty=faculty,
                        books=books,
                        interests=interests,
                        home_town=home_town,
                        career=career
                    )
                    db.session.add(author)
                    db.session.commit()
                    db.session.refresh(author)
            # db.session.commit()
            w = 'Информация скачана!'
        return render_template('search.html', owner_id=some_id, w=w)
    else:
        return redirect(url_for('answer_process'))


@app.route('/form1', methods=['get'])
def date_selection():

    if not request.args.get("owner_id"):
        return redirect(url_for('date_selection'))
    some_id = request.args.get('owner_id')
    if not request.args.get('start_date') or not request.args.get('fin_date'):
        start_date = ''
        fin_date = ''
    elif (not request.args.get('start_date')) and (request.args.get('fin_date')):
        start_date = ''
        fin_date = request.args.get('fin_date')
    elif (request.args.get('start_date')) and (not request.args.get('fin_date')):
        start_date = request.args.get('start_date')
        fin_date = ''
    else:
        start_date = request.args.get('start_date')
        fin_date = request.args.get('fin_date')
    em_post, w_post, em_com, w_com, auth_w_d, post_avg_like, post_weeks, com_avg_like, com_weeks = com_words(some_id,
                                                                                                             start_date,
                                                                                                             fin_date)
    week_url = week_meta_graph(post_weeks, com_weeks)

    em_post_url, em_post_words = com_word_graph(em_post, 'Эмоджи в постах', 'Эмоджи')
    w_post_url, w_post_words = com_word_graph(w_post, 'Слова в постах', 'Слова')
    em_com_url, em_com_words = com_word_graph(em_com, 'Эмоджи в комментариях', 'Эмоджи')
    w_com_url, w_com_words = com_word_graph(w_com, 'Слова в комментариях', 'Слова')
    auth_info = db.session.query(Authors.sex, Authors.month,
                                 Authors.city, Authors.faculty,
                                 Authors.home_town).filter(Authors.id.in_(auth_w_d)).all()
    sex_dict = []
    return render_template('results.html', some_id=some_id, start_date=start_date, fin_date=fin_date,
                           em_post_words=em_post_words, w_post_words=w_post_words, em_com_words=em_com_words,
                           w_com_words=w_com_words, em_post_url=em_post_url, w_post_url=w_post_url,
                           em_com_url=em_com_url, w_com_url=w_com_url, week_url=week_url)


def com_words(owner_id, start_date, fin_date):
    auth_w_d = []
    if start_date != '' and fin_date != '':
        to_date_posts = db.session.query(Posts.lem_text,
                                         Posts.likes,
                                         Posts.weekday,
                                         Posts.author_id).filter(Posts.wall_owner == owner_id,
                                                                 Posts.date_time >= start_date,
                                                                 Posts.date_time <= fin_date).all()
        to_date_coms = db.session.query(Comments.lem_text,
                                        Comments.likes,
                                        Comments.weekday,
                                        Comments.author_id).filter(Comments.wall_owner == owner_id,
                                                                   Comments.date_time >= start_date,
                                                                   Comments.date_time <= fin_date).all()
    elif start_date != '' and fin_date == '':
        to_date_posts = db.session.query(Posts.lem_text,
                                         Posts.likes,
                                         Posts.weekday,
                                         Posts.author_id).filter(Posts.wall_owner == owner_id,
                                                                 Posts.date_time >= start_date).all()
        to_date_coms = db.session.query(Comments.lem_text,
                                        Comments.likes,
                                        Comments.weekday,
                                        Comments.author_id).filter(Comments.wall_owner == owner_id,
                                                                   Comments.date_time >= start_date).all()
    elif start_date == '' and fin_date != '':
        to_date_posts = db.session.query(Posts.lem_text,
                                         Posts.likes,
                                         Posts.weekday,
                                         Posts.author_id).filter(Posts.wall_owner == owner_id,
                                                                 Posts.date_time <= fin_date).all()
        to_date_coms = db.session.query(Comments.lem_text,
                                        Comments.likes,
                                        Comments.weekday,
                                        Comments.author_id).filter(Comments.wall_owner == owner_id,
                                                                   Comments.date_time <= fin_date).all()
    else:
        to_date_posts = db.session.query(Posts.lem_text,
                                         Posts.likes,
                                         Posts.weekday,
                                         Posts.author_id).filter(Posts.wall_owner == owner_id).all()
        to_date_coms = db.session.query(Comments.lem_text,
                                        Comments.likes,
                                        Comments.weekday,
                                        Comments.author_id).filter(Comments.wall_owner == owner_id).all()

    em_post, w_post, auth_w_d, post_avg_like, post_weeks = get_dicts(to_date_posts, auth_w_d)
    em_com, w_com, auth_w_d, com_avg_like, com_weeks = get_dicts(to_date_coms, auth_w_d)
    return em_post, w_post, em_com, w_com, auth_w_d, post_avg_like, post_weeks, com_avg_like, com_weeks


def com_word_graph(com_dict, title, w_type):
    img = io.BytesIO()
    x = []
    words = []
    counts = []
    for key, value in com_dict:
        words.append(key)
        counts.append(value)
    num_words = len(counts)
    for k in range(num_words):
        x.append(k + 1)
    plt.figure(figsize=(15, 10))
    plt.bar(x, counts, color='purple')
    plt.xticks(ticks=x, labels=words)
    plt.title(title)
    plt.ylabel('Кол-во употреблений')
    plt.xlabel(w_type)
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(graph_url), words


def week_meta_graph(post_week, com_week):
    img = io.BytesIO()
    whole_dict = []
    for key in dict(post_week).keys():
        whole_dict.append({'weekday': key, 'type': 'post', 'count': dict(post_week)[key]})
    for key in dict(com_week).keys():
        whole_dict.append({'weekday': key, 'type': 'comment', 'count': dict(com_week)[key]})
    whole_db = pd.DataFrame(whole_dict)
    plt.figure(figsize=(15, 10))
    sns.barplot(x='weekday', y='count', hue='type', order=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    data=whole_db, palette='Purples')
    plt.title('День недели и кол-во записей')
    plt.ylabel('Кол-во запсисей')
    plt.xlabel('День недели')
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(graph_url)

@app.route('/back_to_form1', methods=['get'])
def back():
    if not request.args.get("some_id"):
        return redirect(url_for('index'))
    else:
        some_id = request.args.get("some_id")
        w = 'New date selection.'
        return render_template('search.html', owner_id=some_id, w=w)


if __name__ == '__main__':
    app.run(debug=False)
