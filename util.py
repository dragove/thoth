import ahocorasick
import json
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime, timedelta, date
import uuid
from math import log


# Encoder for sqlalchemy object to convert the object to a json format string
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:  # 添加了对datetime的处理
                    if isinstance(data, datetime):
                        fields[field] = data.isoformat()
                    elif isinstance(data, date):
                        fields[field] = data.isoformat()
                    elif isinstance(data, timedelta):
                        fields[field] = (datetime.min + data).time().isoformat()
                    else:
                        fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


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
    seconds = epoch_seconds(datetime(int(dates[0]), int(dates[1]),
                                     int(dates[2]))) - 1134028003
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
    for item in A.iter(sentence):
        return True
    return False
