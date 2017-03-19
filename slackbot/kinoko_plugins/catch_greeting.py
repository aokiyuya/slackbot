#! $(which python) env
# coding: UTF-8
############################
# Author Yuya Aoki
# this is bot manage sleeping
############################
# import re
from slackbot.bot import respond_to
from slackbot.bot import listen_to
import mysql.connector
import datetime

# table name on mysql
TABLE_NAME = "greeting"

# datanames on mysql
ID = 0
NAME = 1
TIME = 2
STATE = 3

# connect database
conn = mysql.connector.connect(
    user='root', host='localhost', database='kinoko')
cur = conn.cursor()


# insert したら commit しなきゃいけないらしい
def req_commit(string):
    cur.execute(string)
    conn.commit()


# id の一覧を返す
def return_ids():
    ids = []
    cur.execute("select id from " + TABLE_NAME + ";")
    for row in cur.fetchall():
        ids.append(row[0])
    if ids == []:
        return None
    return ids


# おはよう、おやすみのときに呼ばれる
def insert_data(name, status):
    ids = return_ids()
    id = 1 if ids is None else int(max(ids)) + 1
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    string = "insert into {} values ( {} , \'{}\', \'{}\', \'{}\');"
    req_commit(string.format(TABLE_NAME, str(id), name, time, status))


def gen_pretty_time(time):
    hour, minute, second = str(time).split(':')
    return "{}時間{}分{}秒".format(hour, minute, second)


# おやすみのほうがおはようより前だよね?
def is_correct(sleep, awake):
    if sleep is None or awake is None:
        return False
    if sleep > awake:
        return False
    return True


# DB からデータをとってくる
def get_time_line(message, day):
    time_line = []
    time = (datetime.datetime.now()
            - datetime.timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
    req = "select * from {} where time > \'{}\' AND name = \'{}\';"
    cur.execute(req.format(TABLE_NAME, time, message._get_user_id()))
    for row in cur.fetchall():
        time_line.append(row)
    if time_line == []:
        return None
    return time_line


# sleep から始まらないと面倒
def gen_correct_time_line(time_line):
    while True:
        if time_line[0][STATE] == 'awake':
            del time_line[0]
        if time_line[0][STATE] == 'sleep':
            break
    return time_line


# がんばって睡眠時間を計算してる
def calc_sleeping_time(time_line):
    count = 0
    sleeping_time = datetime.timedelta(days=0)
    sleep = None
    for i in range(len(time_line)):
        if time_line[i][STATE] == 'sleep':
            sleep = time_line[i][TIME]
        if time_line[i][STATE] == 'awake' and sleep is not None:
            if is_correct(sleep, time_line[i][TIME]):
                count = count + 1
                sleeping_time = sleeping_time + (time_line[i][TIME] - sleep)
                sleep = None
    return sleeping_time, sleeping_time/count


# 一週間の睡眠時間を求める
def get_weekly_sleeping_time(message):
    time_line = get_time_line(message, 7)
    if time_line is not None:  # 代入する必要ないと思った(小学生並の感想)
        time_line = gen_correct_time_line(time_line)
        sleeping, ave = calc_sleeping_time(time_line)
        string = "合計睡眠時間は{}で、平均は{}です"
        return string.format(gen_pretty_time(sleeping), gen_pretty_time(ave))
    return "バグかも〜"


# 24時間以内の睡眠時間を求める
def get_sleeping_time(message):
    time_line = get_time_line(message, 1)
    if time_line is not None:  # 代入ry
        time_line = gen_correct_time_line(time_line)
        sleeping_time, ave = calc_sleeping_time(time_line)
        return sleeping_time
    return None


@respond_to(u'おはよ')
@respond_to(u'起きた')
@respond_to(u'おきた')
@listen_to(u'おはよ')
@listen_to(u'起きた')
@listen_to(u'おきた')
def hello_reply(message):
    message.reply(u'おはようございます')
    name = message._get_user_id()
    insert_data(name, 'awake')
    sleeping_time_send(message)


@respond_to(u'おやすみ')
@listen_to(u'おやすみ')
@respond_to(u'寝る')
@listen_to(u'寝る')
@respond_to(u'ねる')
@listen_to(u'ねる')
def good_night_reply(message):
    message.reply(u'おやすみなさい')
    name = message._get_user_id()
    insert_data(name, 'sleep')


@respond_to(u'今週')
@listen_to(u'今週')
def weekly_sleeping_reply(message):
    text = get_weekly_sleeping_time(message)
    message.reply(text)


@respond_to(u'今日')
@listen_to(u'今日')
def sleeping_time_reply(message):
    sleeping_time = get_sleeping_time(message)
    if sleeping_time is None:
        text = "something is happen. please check database."
    else:
        text = "今日の睡眠時間は {} でした".format(sleeping_time)
    message.reply(text)


def sleeping_time_send(message):
    sleeping_time = get_sleeping_time(message)
    if sleeping_time is None:
        text = "something is happen. please check database."
    else:
        text = "今日の睡眠時間は {} でした".format(sleeping_time)
    message.send(text)

# @respond_to('^reply_webapi$')
# def hello_webapi(message):
#     message.reply_webapi('hello there!', attachments=[{
#         'fallback': 'test attachment',
#         'fields': [
#             {
#                 'title': 'test table field',
#                 'value': 'test table value',
#                 'short': True
#             }
#         ]
#     }])
#
#
# @respond_to('^reply_webapi_not_as_user$')
# def hello_webapi_not_as_user(message):
#     message.reply_webapi('hi!', as_user=False)
#
#
# @respond_to('hello_formatting')
# def hello_reply_formatting(message):
#     # Format message with italic style
#     message.reply('_hello_ sender!')
#
#
# @listen_to('hello$')
# def hello_send(message):
#     message.send('hello channel!')
#
#
# @listen_to('hello_decorators')
# @respond_to('hello_decorators')
# def hello_decorators(message):
#     message.send('hello!')
#
#
# @listen_to('hey!')
# def hey(message):
#     message.react('eggplant')
#
#
# @respond_to(u'你好')
# def hello_unicode_message(message):
#     message.reply(u'你好!')
