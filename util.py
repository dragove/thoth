import json
import smtplib
import uuid
from datetime import datetime, timedelta, date
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import ahocorasick
from math import log
from sqlalchemy.ext.declarative import DeclarativeMeta


# Encoder for sqlalchemy object to convert the object to a json format string
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [
                    x for x in dir(obj)
                    if not x.startswith('_') and x != 'metadata'
            ]:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(
                        data
                    )  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:  # process datetime
                    if isinstance(data, datetime):
                        fields[field] = data.isoformat()
                    elif isinstance(data, date):
                        fields[field] = data.isoformat()
                    elif isinstance(data, timedelta):
                        fields[field] = (datetime.min +
                                         data).time().isoformat()
                    else:
                        fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


# Input your server information as consts in this class
class CONST:
    SERVER_ADDR = ''
    SMTP_SERVER = ''
    EMAIL_ADDR = ''
    EMAIL_PASSWORD = ''


epoch = datetime(1970, 1, 1)


def epoch_seconds(date):
    td = date - epoch
    return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)


# this function will return a score for articles by update date and votes.
def hot(article):
    ups = article.metric.up_votes
    downs = article.metric.down_votes
    date = article.date
    visits = article.metric.visits
    comments = article.metric.comments
    s = ups / max((ups + downs), 1) * (visits + comments)
    order = log(max(abs(s), 1), 2)
    dates = date.split(' ')[0].split('-')
    seconds = epoch_seconds(
        datetime(int(dates[0]), int(dates[1]), int(dates[2]))) - 1134028003
    return round(order + s * seconds / 450000000, 7)


def get_uuid():
    return str(uuid.uuid4())[0:8]


A = ahocorasick.Automaton()

dirties = []
with open('dirty.txt', 'r') as f:
    words = f.readlines()
    for word in words:
        dirties.append(word.replace('\n', ''))

for idx, key in enumerate(dirties):
    A.add_word(key, (idx, key))

A.make_automaton()


# check whether the sentence has dirty words. If so, this function will return True, otherwise, return False.
def check_dirty(sentence):
    for _ in A.iter(sentence):
        return True
    return False


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


# usage: send_email('dove@thoth.com', 'fcjgh', 'dove@zjnu.edu.cn',
# 'smtp.thoth.com', 'new upload', 'you have a new article upload in thoth')
def send_email(from_addr, password, to_addr, smtp_server, subject, content):
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = _format_addr('<%s>' % from_addr)
    msg['To'] = _format_addr('<%s>' % to_addr)
    msg['Subject'] = Header(subject, 'utf-8').encode()
    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()
