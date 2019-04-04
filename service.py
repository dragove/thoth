from app import db
from model import *


class ArticleService:
    def find_all_articles(self):
        articles = Article.query.filter_by(hidden=0).all()
        return articles

    def find_by_subject(self, subject):
        articles = Article.query.filter_by(hidden=0).filter_by(subject=subject).order_by(Article.date.desc())
        return articles

    def find_by_id(self, id):
        article = Article.query.filter_by(id=id).first()
        return article

    def insert(self, article):
        db.session.add(article)
        db.session.commit()

    def search(self, content):
        articles = Article.query.filter_by(hidden=0).whoosh_search(content)
        return articles

    def find_by_user(self, user):
        articles = Article.query.filter_by(hidden=0).filter_by(user=user)
        return articles

    def set_hidden(self, article, hidden):
        article.hidden = hidden
        db.session.commit()

    def delete(self, article):
        db.session.delete(article)
        db.session.commit()


class SubjectService:
    def find_children(self, subject):
        ret = []
        rs = SubjectTree.query.filter_by(parent_id=subject.id)
        for result in rs:
            ret.append(Subject.query.filter_by(id=result.child_id).first())
        return ret

    def find_parents(self, subject):
        ret = []
        rs = SubjectTree.query.filter_by(child_id=subject.id)
        for result in rs:
            ret.append(Subject.query.filter_by(id=result.parent_id).first())
        return ret

    def find_all(self):
        subjects = Subject.query.filter(Subject.id != '1')
        return subjects

    def find_by_id(self, id):
        subject = Subject.query.filter_by(id=id).first()
        return subject

    def find_by_name(self, name):
        subject = Subject.query.filter_by(name=name).first()
        return subject

    def find_similar_by_name(self, name):
        subject = Subject.query.filter(Subject.similar_name.like('%' + name + '%')).first()
        return subject

    def insert(self, subject, parent_id):
        db.session.add(subject)
        db.session.add(SubjectTree(parent_id=parent_id, child_id=subject.id))
        db.session.commit()


class UserService:
    def find_by_id(self, id):
        user = User.query.filter_by(id=id).first()
        return user

    def find_by_email(self, email):
        user = User.query.filter_by(email=email).first()
        return user

    def insert(self, user):
        db.session.add(user)
        db.session.commit()


class CommentService:
    def insert(self, comment):
        db.session.add(comment)
        db.session.commit()

    def find_by_id(self, id):
        return Comment.query.filter_by(id=id).first()

    def find_by_email(self, email):
        return Comment.query.filter_by(email=email)

    def up_vote(self, comment_id, ip_id):
        comment = self.find_by_id(comment_id)
        current = self.get_current_vote(comment_id, ip_id)
        if current is None:
            db.session.add(CommentIP(ip_id=ip_id, comment_id=comment_id, vote=1))
            comment.up_votes += 1
        else:
            if current.vote == 1:
                current.vote = 0
                comment.up_votes -= 1
            elif current.vote == 2:
                comment.up_votes += 1
                comment.down_votes -= 1
                current.vote = 1
            else:
                comment.up_votes += 1
                current.vote = 1
        db.session.commit()

    def down_vote(self, comment_id, ip_id):
        comment = self.find_by_id(comment_id)
        current = self.get_current_vote(comment_id, ip_id)
        if current is None:
            db.session.add(CommentIP(ip_id=ip_id, comment_id=comment_id, vote=2))
            comment.down_votes += 1
        else:
            if current.vote == 2:
                current.vote = 0
            else:
                if current.vote == 2:
                    current.vote = 0
                    comment.down_votes -= 1
                elif current.vote == 1:
                    comment.up_votes -= 1
                    comment.down_votes += 1
                    current.vote = 2
                else:
                    comment.down_votes += 1
                    current.vote = 2
        db.session.commit()

    def get_current_vote(self, comment_id, ip_id):
        current = CommentIP.query.filter_by(ip_id=ip_id) \
            .filter_by(comment_id=comment_id).first()
        return current

    def search(self, content):
        comments = Comment.query.whoosh_search(content)
        return comments

    def delete(self, comment):
        db.session.delete(comment)
        db.session.commit()

class IPService:
    def get_by_ip(self, addr):
        ip = IP.query.filter_by(addr=addr).first()
        return ip

    def insert(self, ip):
        db.session.add(ip)
        db.session.commit()


class MetricService:
    def add_visit(self, article_id):
        current = Metric.query.filter_by(article_id=article_id).first()
        current.visits += 1
        db.session.commit()

    def add_comments(self, article_id):
        current = Metric.query.filter_by(article_id=article_id).first()
        current.comments += 1
        db.session.commit()

    def up_vote(self, article_id, ip_id):
        current = self.get_current_vote(article_id, ip_id)
        metric = Metric.query.filter_by(article_id=article_id).first()
        if current is None:
            db.session.add(ArticleIP(ip_id=ip_id, article_id=article_id, vote=1))
            metric.up_votes += 1
        else:
            if current.vote == 1:
                current.vote = 0
                metric.up_votes -= 1
            elif current.vote == 2:
                current.vote = 1
                metric.up_votes += 1
                metric.down_votes -= 1
            else:
                current.vote = 1
                metric.up_votes += 1
        db.session.commit()

    def down_vote(self, article_id, ip_id):
        current = self.get_current_vote(article_id, ip_id)
        metric = Metric.query.filter_by(article_id=article_id).first()
        if current is None:
            db.session.add(ArticleIP(ip_id=ip_id, article_id=article_id, vote=2))
            metric.down_votes += 1
        else:
            if current.vote == 2:
                current.vote = 0
                metric.down_votes -= 1
            elif current.vote == 1:
                current.vote = 2
                metric.up_votes -= 1
                metric.down_votes += 1
            else:
                current.vote = 2
                metric.down_votes += 1
        db.session.commit()

    def get_current_vote(self, article_id, ip_id):
        current = ArticleIP.query.filter_by(ip_id=ip_id) \
            .filter_by(article_id=article_id).first()
        return current

    def set_visited(self, article_id, ip_id):
        db.session.add(ArticleIP(ip_id=ip_id, article_id=article_id, vote=0))
        db.session.commit()


article_service = ArticleService()
ip_service = IPService()
user_service = UserService()
metric_service = MetricService()
comment_service = CommentService()
subject_service = SubjectService()
if __name__ == "__main__":
    pass
