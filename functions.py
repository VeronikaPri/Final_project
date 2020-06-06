import conf
from tqdm.auto import tqdm
import time
import re
import requests
import math
from emoji.unicode_codes import UNICODE_EMOJI
from pymorphy2 import MorphAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from flask import render_template
import datetime
import pandas as pd
from collections import Counter
morph = MorphAnalyzer()
sw = stopwords.words('russian')

st_w_ru = ['без', 'более', 'бы', 'был', 'была', 'были', 'было', 'быть', 'вам', 'вас', 'ведь', 'весь', 'вдоль', 'вместо',
           'вне', 'вниз', 'внизу', 'внутри', 'во', 'вокруг', 'вот', 'все', 'всегда', 'всего', 'всех', 'вы', 'где', 'да',
           'давай', 'давать', 'даже', 'для', 'до', 'достаточно', 'его', 'ее', 'её', 'если', 'есть', 'ещё', 'же', 'за',
           'за исключением', 'здесь', 'из', 'из-за', 'или', 'им', 'иметь', 'их', 'как', 'как-то', 'кто', 'когда',
           'кроме', 'кто', 'ли', 'либо', 'мне', 'может', 'мои', 'мой', 'мы', 'на', 'навсегда', 'над', 'надо', 'наш',
           'не', 'него', 'неё', 'нет', 'ни', 'них', 'но', 'ну', 'об', 'однако', 'он', 'она', 'они', 'оно', 'от',
           'отчего', 'очень', 'по', 'под', 'после', 'потому', 'потому', 'что', 'почти', 'при', 'про', 'снова',
           'со', 'так', 'также', 'такие', 'такой', 'там', 'те', 'тем', 'то', 'того', 'тоже', 'той', 'только', 'том',
           'тут', 'ты', 'уже', 'хотя', 'чего', 'чего-то', 'чей', 'чем', 'что', 'чтобы', 'чьё', 'чья', 'эта', 'эти',
           'это']
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
    add_sw = ['это', 'мочь', 'делать', 'знать', 'хотеть', 'весь', 'год', 'очень', 'сказать', 'день']
    tockenized = word_tokenize(text)
    filtered = ""
    for w in tockenized:
        w.strip(p)
        if w not in sw and w not in add_sw and w not in punkt:
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
    ).json()['response']['items']
    for com in raw_comments:
        if com.get('text') is not None:
            if com['text'] != '':
                if com['id'] not in comment_ids:
                    com_block = {}
                    com_block['id'] = com['id']
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
                        post['id'] = item.get('id')
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

def search(user_type, id_type, some_id):
    all_comments = []
    all_posts = []
    all_authors = []
    comment_ids = []
    post_ids = []
    author_ids = []
    message = ''

    # если работаем с айди юзера
    if user_type == 'user':
        if id_type == 'short_name':
            # print("short_name!")
            data = requests.get(
                'https://api.vk.com/method/users.get',
                params={
                    'user_ids': some_id,
                    'access_token': conf.token,
                    'v': "5.92"}).json()
            if data.get('response'):
                some_id = data['response'][0]['id']
            else:
                message = 'error 0! No response. Try another user.'
                # print(data)
        elif id_type == 'numeric':
            pass
            # если работаем с айди группы
    elif user_type == 'group':
        if id_type == 'short_name':
            # print('short_name!')
            data = requests.get(
                'https://api.vk.com/method/groups.getById',
                params={
                    'group_ids': some_id,
                    'access_token': conf.token,
                    'v': "5.92"}).json()
            if data.get('response'):
                resp = data['response'][0]
                some_id = resp['id']
                # print(some_id)
            else:
                message = 'error 0! No response. Try another user.'
                # print(data)
        elif id_type == 'numeric':
            pass
    else:
        message = 'Неверный тип id. Можно либо группу, либо пользователя.'

    if message == '':
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
            return all_comments, all_posts, all_authors
        else:
            return render_template('error.html', message=message)
    else:
        return render_template('error.html', message=message)


def get_dicts(to_date_posts, auth_w_d):
    w_d = []
    punkt = ['"', ',', '.', '!', '?', ':', ';', ')', '(', '...', '``', '—', '#', '..', '«', '»', '-', '*', '[', ']',
             '--']
    add_sw = ['это', 'мочь', 'делать', 'знать', 'хотеть', 'весь', 'год', 'очень', 'сказать', 'день', 'человек', 'никто',
              'просто', 'понять']
    for item in to_date_posts:
        lem_text = item[0]
        likes = item[1]
        weekday = item[2]
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
    w_df = pd.DataFrame(w_d)
    em = w_df[w_df.type.isin(['emoji'])]
    w = w_df[w_df.type.isin(['word'])]
    em_d = Counter(list(em['word'])).most_common(10)
    wr_d = Counter(list(w['word'])).most_common(10)
    return em_d, wr_d, auth_w_d


