from app import app
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee

db = SQLAlchemy(app)
whooshee = Whooshee(app)


@whooshee.register_model('title', 'abstract', 'highlight_part', 'author')
class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Text, primary_key=True)
    title = db.Column(db.Text)
    abstract = db.Column(db.Text)
    highlight_part = db.Column(db.Text)
    date = db.Column(db.Text)
    comments = db.relationship('Comment', lazy='subquery')
    subject_id = db.Column(db.Text, db.ForeignKey('subject.id'))
    subject = db.relationship('Subject', lazy='subquery')
    metric = db.relationship('Metric', uselist=False, lazy='subquery')
    user_id = db.Column(db.Text, db.ForeignKey('user.id'))
    user = db.relationship('User', lazy='subquery')
    hidden = db.Column(db.Integer, default=0)
    score = 0.0
    author = db.Column(db.Text)
    pdf = db.Column(db.BLOB)


@whooshee.register_model('text')
class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Text, primary_key=True)
    email = db.Column(db.Text)
    text = db.Column(db.Text)
    up_votes = db.Column(db.Integer, default=0)
    down_votes = db.Column(db.Integer, default=0)
    article_id = db.Column(db.Text, db.ForeignKey('article.id'))
    article = db.relationship('Article', lazy='subquery')


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Text, primary_key=True)
    email = db.Column(db.Text, unique=True)
    is_blocked = db.Column(db.Integer, default=0)


class SubjectTree(db.Model):
    __tablename__ = 'subject_tree'
    parent_id = db.Column(db.Text,
                          db.ForeignKey('subject.id'),
                          primary_key=True)
    child_id = db.Column(db.Text,
                         db.ForeignKey('subject.id'),
                         primary_key=True)


class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, unique=True)
    similar_name = db.Column(db.Text)
    articles = db.relationship('Article')


class Metric(db.Model):
    __tablename__ = 'metric'
    id = db.Column(db.Text, primary_key=True)
    visits = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    up_votes = db.Column(db.Integer, default=0)
    down_votes = db.Column(db.Integer, default=0)
    article_id = db.Column(db.Text, db.ForeignKey('article.id'))
    article = db.relationship('Article')


class IP(db.Model):
    __tablename__ = 'ip'
    id = db.Column(db.Text, primary_key=True)
    addr = db.Column(db.Text)
    is_blocked = db.Column(db.Integer, default=0)


class CommentIP(db.Model):
    __tablename__ = 'comment_ip'
    ip_id = db.Column(db.Text, db.ForeignKey('ip.id'), primary_key=True)
    comment_id = db.Column(db.Text,
                           db.ForeignKey('comment.id'),
                           primary_key=True)
    vote = db.Column(db.Integer, default=0)


class ArticleIP(db.Model):
    __tablename__ = 'article_ip'
    ip_id = db.Column(db.Text, db.ForeignKey('ip.id'), primary_key=True)
    article_id = db.Column(db.Text,
                           db.ForeignKey('article.id'),
                           primary_key=True)
    vote = db.Column(db.Integer, default=0)


whooshee.reindex()

if __name__ == "__main__":
    db.drop_all()
    db.create_all()
