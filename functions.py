import conf
from tqdm.auto import tqdm
import time
import re
import requests
import math
from emoji.unicode_codes import UNICODE_EMOJI
from pymorphy2 import MorphAnalyzer
from nltk.tokenize import word_tokenize
from flask import render_template
import datetime
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
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
           'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между','без',
           'более', 'бы', 'был', 'была', 'были', 'было', 'быть', 'вам', 'вас', 'ведь', 'весь', 'вдоль', 'вместо',
           'вне', 'вниз', 'внизу', 'внутри', 'во', 'вокруг', 'вот', 'все', 'всегда', 'всего', 'всех', 'вы', 'где', 'да',
           'давай', 'давать', 'даже', 'для', 'до', 'достаточно', 'его', 'ее', 'её', 'если', 'есть', 'ещё', 'же', 'за',
           'за исключением', 'здесь', 'из', 'из-за', 'или', 'им', 'иметь', 'их', 'как', 'как-то', 'кто', 'когда',
           'кроме', 'кто', 'ли', 'либо', 'мне', 'может', 'мои', 'мой', 'мы', 'на', 'навсегда', 'над', 'надо', 'наш',
           'не', 'него', 'неё', 'нет', 'ни', 'них', 'но', 'ну', 'об', 'однако', 'он', 'она', 'они', 'оно', 'от',
           'отчего', 'очень', 'по', 'под', 'после', 'потому', 'потому', 'что', 'почти', 'при', 'про', 'снова',
           'со', 'так', 'также', 'такие', 'такой', 'там', 'те', 'тем', 'то', 'того', 'тоже', 'той', 'только', 'том',
           'тут', 'ты', 'уже', 'хотя', 'чего', 'чего-то', 'чей', 'чем', 'что', 'чтобы', 'чьё', 'чья', 'эта', 'эти',
           'это', 'это', 'мочь', 'делать', 'знать', 'хотеть', 'весь', 'год', 'очень', 'сказать', 'день']
def norm_time(sec):
    months = {'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
              'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
              'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08'}
    date = time.ctime(int(sec))
    pattern = '([A-Za-z]+) ([A-Za-z]+)( )+([0-9]+) ([0-9:]+) ([0-9]+)'
    pattern1 = '[0-9]+\:[0-9]+\:[0-9]+'
    result = re.search(pattern, date)
    if result:
        weekday = result.group(1)
        month = result.group(2)
        day = result.group(4)
        clock = result.group(5)
        year = result.group(6)
        norm_date = year + '-' + months[month] + '-' + day
        new_date = datetime.datetime.strptime(str(norm_date), '%Y-%m-%d')
        date_time = new_date.strftime('%Y-%m-%d') + ' ' + clock
    else:
        date_time = weekday = None
    return date_time, weekday


def text_vs_emojis(string):
    emojis = ' '.join(c for c in string if c in UNICODE_EMOJI)
    text = ''.join(c for c in string if c not in UNICODE_EMOJI)
    return text, emojis


def lemmatize(text):
    p = '",.!?:;)(...``—#..«»-'
    punkt = ['"', ',', '.', '!', '?', ':', ';', ')', '(', '...', '``', '—', '#', '..', '«', '»', '-']
    tockenized = word_tokenize(text)
    filtered = ""
    for w in tockenized:
        w.strip(p)
        if w not in sw and w not in punkt:
            w, emojis = text_vs_emojis(w)
            ana = morph.parse(w)
            first = ana[0]
            norm_w = first.normal_form
            filtered = filtered + " " + str(norm_w) + " " + str(emojis)
    filtered = filtered.strip(" ")
    return filtered


def get_comments(user_id, post_id, offset, comment_ids, author_ids, all_comments):
    raw_comments = requests.get(
        'https://api.vk.com/method/wall.getComments',
        params={
            "owner_id": user_id,
            "post_id": post_id,
            "count": 100,
            "offset": offset,
            "need_likes": 1,
            "v": "5.92",
            "access_token": conf.token}
    ).json()
    if raw_comments.get('response'):
        raw_comments = raw_comments['response']['items']
        for com in raw_comments:
            if com.get('text') is not None:
                if com['text'] != '':
                    if com['id'] not in comment_ids:
                        com_block = {}
                        com_block['id'] = str(com['id']) + str(com['post_id'])
                        com_block['post_id'] = com['post_id']
                        com_block['author_id'] = com['from_id']
                        if com['from_id'] not in author_ids:
                            author_ids.append(com['from_id'])
                        com_block['text'] = com['text']
                        com_block['lem_text'] = lemmatize(com['text'])
                        com_block['likes'] = com['likes'].get('count')
                        date_time, weekday = norm_time(com['date'])
                        com_block['date_time'] = date_time
                        com_block['weekday'] = weekday
                        com_block['wall_owner'] = user_id
                        all_comments.append(com_block)
                        comment_ids.append(com['id'])
    else:
        pass
    return all_comments, author_ids, comment_ids


def get_user_posts(user_id, offset, post_ids, author_ids, all_posts, comment_ids, all_comments):
    wall_items = requests.get(
        'https://api.vk.com/method/wall.get',
        params={
            "owner_id": user_id,
            "count": 100,
            "offset": offset,
            "v": "5.92",
            "access_token": conf.token}
    ).json()
    if wall_items.get('response') is not None:
        wall_items = wall_items['response']['items']
        for item in wall_items:
            if item.get('copy_history') is None:
                if item.get('text') != '':
                    if item.get('id') not in post_ids:
                        post = {}
                        post['id'] = str(item.get('id')) + str(item.get('owner_id'))
                        post['user_id'] = item.get('owner_id')
                        if item.get('owner_id') not in author_ids:
                            author_ids.append(item.get('owner_id'))
                        post['text'] = item.get('text')
                        post['lem_text'] = lemmatize(post['text'])
                        post['likes'] = item['likes'].get('count')
                        if item.get('date'):
                            date_time, weekday = norm_time(item['date'])
                        else:
                            date_time = weekday = None
                        post['date_time'] = date_time
                        post['weekday'] = weekday
                        post['wall_owner'] = user_id
                        all_posts.append(post)
                        post_ids.append(item.get('id'))
                        # заодно соберем комментарии, если они есть
                        if item['comments'].get('count') > 0:
                            total_com = item['comments'].get('count')
                            offset_num = math.ceil(total_com / 100)
                            off_x = -100
                            for i in range(offset_num):
                                off_x += 100
                                get_comments(user_id, post['id'], off_x, comment_ids, author_ids, all_comments)
        return all_posts, all_comments, author_ids, post_ids, comment_ids
    else:
        return None


def birth_date(bdate):
    pattern1 = '([0-9]+)\.([0-9]+)\.([0-9]+)'
    pattern2 = '([0-9]+)\.([0-9]+)'
    result = re.search(pattern1, bdate)
    if result:
        day = result.group(1)
        month = result.group(2)
        year = result.group(3)
    else:
        result = re.search(pattern2, bdate)
        if result:
            day = result.group(1)
            month = result.group(2)
            year = None
        else:
            day = month = year = None
    return bdate, day, month, year


def extract_user_info(user_id, all_authors):
    sex_dict = {0: '', 1: 'ж', 2: 'м'}
    users_data = requests.get(
        'https://api.vk.com/method/users.get',
        params={
            'user_ids': str(user_id),
            'access_token': conf.token,
            'v': "5.92",
            'fields': 'sex, bdate, books, career, city, education, followers_count, home_town, interests'}
    ).json()
    if users_data.get('response'):
        users_data = users_data['response'][0]
        city = users_data.get('city')
        if city is not None:
            city = city.get('title')
        else:
            city = None
        if users_data.get('career'):
            career = users_data['career'][0].get('position')
        else:
            career = None
        if users_data.get('bdate'):
            bdate, day, month, year = birth_date(users_data['bdate'])
        else:
            bdate = day = month = year = None
        if users_data.get('books'):
            books = users_data.get('books')
        else:
            books = ''
        if users_data.get('interests'):
            interests = users_data.get('interests')
        else:
            interests = ''
        if users_data.get('home_town'):
            home_town = users_data.get('home_town')
        else:
            home_town = ''
        user_info = {'id': users_data['id'],
                     'sex': sex_dict[users_data['sex']],
                     'bdate': bdate,
                     'day': day,
                     'month': month,
                     'year': year,
                     'city': city,
                     'faculty': users_data.get('faculty_name'),
                     'books': books,
                     'interests': interests,
                     'home_town': home_town,
                     'career': career
                     }
        if user_info not in all_authors:
            all_authors.append(user_info)
        return all_authors
    else:
        return None


def search(some_id):
    all_comments = []
    all_posts = []
    all_authors = []
    comment_ids = []
    post_ids = []
    author_ids = []
    message = ''
    wall_items = requests.get(
        'https://api.vk.com/method/wall.get',
        params={
            "owner_id": some_id,
            "v": "5.92",
            "access_token": conf.token}
        ).json()
    if wall_items.get('response') is not None:
        total_posts = wall_items['response']['count']
        if total_posts > 0:
            off_num = math.ceil(total_posts / 100)
            off = -100
            for i in tqdm(list(range(off_num))):
                off += 100
                get_user_posts(some_id, off, post_ids, author_ids, all_posts, comment_ids, all_comments)
        else:
            message = 'no posts for this user'
    else:
        er_type = str(wall_items['error']['error_code']) + " - " + wall_items['error']['error_msg']
        message = 'Не можем получить доступ к стене :(' + '\n' + er_type
    for user in tqdm(author_ids):
        extract_user_info(user, all_authors)
    if message == '':
        info = [all_comments, all_posts, all_authors]
        return info
    else:
        return ['error.html', message]


def get_dicts(to_date_posts, auth_w_d):
    w_d = []
    weeks = []
    liking = []
    punkt = ['"', ',', '.', '!', '?', ':', ';', ')', '(', '...', '``', '—', '#', '..', '«', '»', '-', '*', '[', ']',
             '--']
    add_sw = ['человек', 'никто', 'просто', 'понять', 'http', 'ваш', 'твой', 'который', 'каждый', 'самый']
    for item in to_date_posts:
        lem_text = item[0]
        likes = item[1]
        liking.append(likes)
        weekday = item[2]
        weeks.append(weekday)
        author_id = item[3]
        tokenized = word_tokenize(lem_text)
        auth_w_d.append(author_id)
        for tok in tokenized:
            if tok in UNICODE_EMOJI:
                type_ = 'emoji'
            else:
                type_ = 'word'
            if tok not in sw and tok not in punkt and tok not in add_sw:
                w_d.append({'word': tok, 'type': type_, 'likes': likes, 'weekday': weekday})
    avg_like = 0
    for like in liking:
        avg_like += int(like)
    try:
        avg_like = round(avg_like/len(liking))
    except ZeroDivisionError:
        avg_like = 0
    weeks = Counter(weeks)
    w_df = pd.DataFrame(w_d)
    em = w_df[w_df['type'].isin(['emoji'])]
    w = w_df[w_df['type'].isin(['word'])]
    em_d = Counter(list(em['word'])).most_common(10)
    wr_d = Counter(list(w['word'])).most_common(10)
    return em_d, wr_d, auth_w_d, avg_like, weeks


def week_meta_graph(post_week, com_week):
    w = 'ok'
    img = io.BytesIO()
    whole_dict = []
    if post_week is not None:
        for key in dict(post_week).keys():
            whole_dict.append({'weekday': key, 'type': 'post', 'count': dict(post_week)[key]})
        if com_week is not None:
            for key in dict(com_week).keys():
                whole_dict.append({'weekday': key, 'type': 'comment', 'count': dict(com_week)[key]})
        else:
            w = 'not_ok'
        whole_db = pd.DataFrame(whole_dict)
        plt.figure(figsize=(10, 5))
        sns.set(font='Century', rc={'axes.facecolor': 'peachpuff', 'figure.facecolor': 'peachpuff'})
        if w == 'ok':
            sns.barplot(x='weekday', y='count', hue='type', order=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                            data=whole_db, palette='Purples')
        else:
            sns.barplot(x='weekday', y='count', order=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        data=whole_db, palette='Purples')
        plt.title('День недели и кол-во записей', fontname='Century')
        plt.ylabel('Кол-во запсисей', fontname='Century')
        plt.xlabel('День недели', fontname='Century')
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return 'data:image/png;base64,{}'.format(graph_url)
    else:
        return 'no posts'


def com_word_graph(com_dict, title, w_type):
    img = io.BytesIO()
    x = []
    words = []
    counts = []
    if com_dict is not None:
        for key, value in com_dict:
            words.append(key)
            counts.append(value)
        num_words = len(counts)
        for k in range(num_words):
            x.append(k + 1)
        plt.figure(figsize=(10, 5))
        plt.bar(x, counts, color='purple')
        plt.xticks(ticks=x, labels=words, fontname='Century')
        plt.title(title, fontname='Century')
        plt.ylabel('Кол-во употреблений', fontname='Century')
        plt.xlabel(w_type, fontname='Century')
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return 'data:image/png;base64,{}'.format(graph_url), words
    else:
        return 'no posts', 'no posts'


def pie_fig(df_col, title):
    img = io.BytesIO()
    plt.figure(figsize=(5, 5))
    df_col.value_counts().plot(kind='pie', cmap=plt.cm.cool, fontsize=10, figsize=(6, 6))
    plt.ylabel(None)
    plt.title(title, fontname='Century')
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(graph_url)


def author_meta(auth_info):
    m_dict = {'1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
              '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec', 'None': 'not_shown'}
    all_meta = []
    for item in auth_info:
        sex = item[0]
        month = m_dict[str(item[1])]
        city = item[2]
        h_t = item[3]
        all_meta.append({'sex': sex, 'month': month, 'city': city, 'h_t': h_t})
    df = pd.DataFrame(all_meta)
    if df.empty:
        sex_meta = month_meta = city_meta = h_t_meta = 'no info'
    else:
        sex_meta = pie_fig(df['sex'], 'Пол авторов')
        month_meta = pie_fig(df['month'], 'Месяц рождения авторов')
        city_meta = pie_fig(df['city'], 'Город проживания авторов')
        h_t_meta = pie_fig(df['h_t'], 'Родной город авторов')
    return sex_meta, month_meta, city_meta, h_t_meta
