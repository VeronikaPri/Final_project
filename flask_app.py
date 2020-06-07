import sqlalchemy
from flask import Flask, render_template, request, redirect, url_for, session
from pymorphy2 import MorphAnalyzer
from functions import search, get_dicts, week_meta_graph, com_word_graph, author_meta
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import sys
sys.path.append(r"C:\Users\Veronuka\AppData\Roaming\Python\Python38\site-packages")
morph = MorphAnalyzer()
sw = ['и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то',
           'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы',
           'по', 'только', 'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о',
           'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже',
           'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж',
           'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут',
           'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам',
           'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж',
           'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним',
           'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас',
           'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два',
           'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас',
           'про', 'всего', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя',
           'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том',
           'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между']

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
    id = db.Column(db.Text, primary_key=True)
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
    id = db.Column(db.Text, primary_key=True)
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
    some_id = request.args.get('some_id')
    if some_id:
        owner_list = []
        owner_stats = db.session.query(Posts.wall_owner).all()
        for item in owner_stats:
            owner_list.append(str(item[0]))
        if str(some_id) in owner_list:
            w = 'Информация об этом пользователе уже есть.'
            return render_template('search.html', owner_id=some_id, w=w)
        else:
            info = search(some_id)
            if len(info) == 2:
                return render_template(info[0], message=info[1])
            else:
                all_comments, all_posts, all_authors = info[0], info[1], info[2]
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
                    try:
                        db.session.add(post)
                        db.session.commit()
                        db.session.refresh(post)
                    except sqlalchemy.exc.InvalidRequestError:
                        db.session.rollback()
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
                    try:
                        db.session.add(comment)
                        db.session.commit()
                        db.session.refresh(comment)
                    except:
                        pass
                # authors
                author_base = []
                author_stats = db.session.query(Authors.id).all()
                for item in author_stats:
                    author_base.append(str(item[0]))
                for index, row in auth_df.iterrows():
                    if str(row['id']) not in author_base:
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
        return render_template('search.html', owner_id=some_id, w=w, all_comments=all_comments, all_posts=all_posts,
                               all_authors=all_authors, info= info)
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
                                 Authors.city,
                                 Authors.home_town).filter(Authors.id.in_(auth_w_d)).all()

    sex_meta, month_meta, city_meta, h_t_meta = author_meta(auth_info)

    if start_date == '':
        start_date = '(не задано)'
    if fin_date == '':
        fin_date = '(не задано)'
    return render_template('results.html', some_id=some_id, start_date=start_date, fin_date=fin_date,
                           em_post_words=em_post_words, w_post_words=w_post_words, em_com_words=em_com_words,
                           w_com_words=w_com_words, em_post_url=em_post_url, w_post_url=w_post_url,
                           em_com_url=em_com_url, w_com_url=w_com_url, week_url=week_url, sex_meta=sex_meta,
                           month_meta=month_meta, city_meta=city_meta, h_t_meta=h_t_meta)


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
    if to_date_posts:
        em_post, w_post, auth_w_d, post_avg_like, post_weeks = get_dicts(to_date_posts, auth_w_d)
    else:
        em_post = w_post = auth_w_d = post_avg_like = post_weeks = None
    if to_date_coms:
        em_com, w_com, auth_w_d, com_avg_like, com_weeks = get_dicts(to_date_coms, auth_w_d)
    else:
        em_com = w_com = com_avg_like = com_weeks = None
    return em_post, w_post, em_com, w_com, auth_w_d, post_avg_like, post_weeks, com_avg_like, com_weeks


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
