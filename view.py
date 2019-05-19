import random
import re
import time
from io import BytesIO

from PIL import Image, ImageFont, ImageDraw
from flask import render_template, request, send_file, abort, redirect, session, make_response

from service import *
from util import *


# this function is for recording different ips and distinguish blocked ips. If the ip is blocked, the visitor will
# got a 403 forbidden page.
@app.before_request
def before_request():
    addr = request.remote_addr
    ip = ip_service.get_by_ip(addr)
    if ip is None:
        ip = IP(id=get_uuid(), addr=addr, is_blocked=0)
        ip_service.insert(ip)
    elif ip.is_blocked == 1:
        abort(403)


# home page function, this page will show all subjects and you can add new subject on this page.
@app.route('/')
def home():
    subjects = []
    first_level = subject_service.find_children(Subject(id='1'))
    for single_subject in first_level:
        second = {'parent': single_subject,
                  'children': []}
        second_level = subject_service.find_children(single_subject)
        for s in second_level:
            second['children'].append(s)
        subjects.append(second)
    return render_template('index.html', subjects=subjects)


# restful api for fetching subjects information.
@app.route('/subjects')
def all_subjects():
    subjects = subject_service.find_all()
    subjects = list(subjects)
    return json.dumps(subjects, cls=AlchemyEncoder)


# return a page shows all article with related subject
@app.route('/subject/<subject_id>')
def subject(subject_id):
    hot_threshold = 450
    subject = subject_service.find_by_id(subject_id)
    articles = article_service.find_by_subject(subject)
    for article in articles:
        article.score = hot(article)
    hot_articles = list(articles)
    print(hot_articles)
    temp_articles = hot_articles[:]
    for article in hot_articles:
        if article.score < hot_threshold:
            temp_articles.remove(article)
    hot_articles = temp_articles
    hot_articles.sort(key=lambda elem: elem.score, reverse=True)
    if len(hot_articles) > 10:
        hot_articles = hot_articles[0:10]
    parents = subject_service.find_parents(subject)
    children = subject_service.find_children(subject)
    return render_template('subject.html', subject=subject, hot_articles=hot_articles,
                           articles=articles, parents=parents, children=children)


# add a subject
@app.route('/subject/add', methods=['POST'])
def add_subject():
    subject_name = request.form['subjectName']
    if subject_name == '':
        return 'Please input subject name'
    parent_id = request.form['parentId']
    similar_name = subject_name.lower()
    similar = subject_service.find_similar_by_name(similar_name)
    if similar is not None:
        return 'Do you mean "' + \
               similar.name + '"? this subject is already exists, ' \
                              'if not, please contact with the website manager.'
    words = subject_name.split()
    cap_letter = ''
    without_space = ''
    for word in words:
        cap_letter += word[0]
        without_space += word
    similar_name += ' ' + cap_letter.lower() + ' ' + without_space.lower()
    if subject_service.find_by_name(subject_name) is None:
        subject_service.insert(Subject(id=get_uuid(), name=subject_name,
                                       similar_name=similar_name), parent_id)
        return 'Insert Successfully'
    return 'This subject is already there'


# upload a new article
@app.route('/upload', methods=['POST'])
def upload():
    form = request.form
    if form['subject'] == "":
        return 'Please select a subject<a href="/upload">return</a>'
    file = request.files['pdf'].read()
    filename = request.files['pdf'].filename
    split = filename.split('.')
    if len(split) != 2 or split[1] != 'pdf':
        return 'unsupported file type, we only receive pdf<a href="/upload">return</a>'
    email = form['email']
    re_str = r'^(\w)+(\.\w+)*@(\w)+((\.\w+)+)$'
    if not re.match(re_str, email):
        return '<h2>Invalid email address</h2>'
    user = user_service.find_by_email(email)
    if user is None:
        user = User(id=get_uuid(), email=email, is_blocked=0)
        user_service.insert(user)
    else:
        if user.is_blocked == 1:
            return 'You are Blocked'
    subject = subject_service.find_by_id(form['subject'])
    if not subject:
        return '<h2>There is no such subject, ' \
               'please create the subject first.</h2>'
    if session['captcha'].lower() != form['captcha'].lower():
        return 'Wrong captcha'
    if check_dirty(form['highlight_part']) or check_dirty(form['abstract']):
        return 'Your article contains dirty words, please try again'
    if session.__contains__('last_article_upload'):
        if time.time() - session['last_article_upload'] < 300:
            return 'You submit articles too frequently, please upload later!!!'
    session['last_article_upload'] = time.time()
    article = Article(id=get_uuid(), pdf=file, title=form['title'],
                      date=time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time())),
                      abstract=form['abstract'], author=form['author'],
                      highlight_part=form['highlight_part'],
                      subject_id=subject.id, metric=Metric(id=get_uuid()),
                      user=user)
    article_service.insert(article)
    return redirect('/article/' + article.id)


# return upload page
@app.route('/upload', methods=['GET'])
def upload_page():
    subjects = subject_service.find_all()
    return render_template('uploadPage.html', subjects=subjects)


# return article page
@app.route('/article/<article_id>')
def article(article_id):
    article = article_service.find_by_id(article_id)
    article.score = hot(article)
    article.comments.reverse()
    ip_id = ip_service.get_by_ip(request.remote_addr).id
    current_vote = metric_service.get_current_vote(article_id, ip_id)
    if current_vote is None:
        metric_service.add_visit(article_id)
        metric_service.set_visited(article_id, ip_id)
    parent = subject_service.find_parents(article.subject)[0]
    return render_template('article.html', article=article, parent=parent)


# up vote articles.
@app.route('/article/<article_id>/up_vote', methods=['POST'])
def article_up_vote(article_id):
    ip_id = ip_service.get_by_ip(request.remote_addr).id
    metric_service.up_vote(article_id, ip_id)
    return 'vote successfully'


# down vote articles.
@app.route('/article/<article_id>/down_vote', methods=['POST'])
def article_down_vote(article_id):
    ip_id = ip_service.get_by_ip(request.remote_addr).id
    metric_service.down_vote(article_id, ip_id)
    return 'vote successfully'


# Upload a comment to article
@app.route('/article/<article_id>/comment', methods=['POST'])
def comment(article_id):
    comment_text = request.form['comment']
    email = request.form['email']
    if session['captcha'].lower() != request.form['captcha']:
        return 'Wrong Captcha'
    if check_dirty(comment_text):
        return 'your comment contains dirty words'
    if session.__contains__('last_comment_upload'):
        if time.time() - session['last_comment_upload'] < 300:
            return 'Please do not comment article too frequently'
    session['last_comment_upload'] = time.time()
    comment_service.insert(Comment(id=get_uuid(), email=email, text=comment_text, article_id=article_id))
    metric_service.add_comments(article_id)
    return 'comment post successfully'


# up vote comment
@app.route('/comment/<comment_id>/up_vote', methods=['POST'])
def up_vote_comment(comment_id):
    ip_id = ip_service.get_by_ip(request.remote_addr).id
    comment_service.up_vote(comment_id, ip_id)
    return 'vote successfully'


# down vote comment
@app.route('/comment/<comment_id>/down_vote', methods=['POST'])
def down_vote_comment(comment_id):
    ip_id = ip_service.get_by_ip(request.remote_addr).id
    comment_service.down_vote(comment_id, ip_id)
    return 'vote successfully'


# Download PDF
@app.route('/article/<article_id>/pdf')
def pdf(article_id):
    article = article_service.find_by_id(article_id)
    bio = BytesIO()
    bio.write(article.pdf)
    bio.seek(0)
    return send_file(bio, attachment_filename="%s.pdf" % article.title, as_attachment=True, mimetype='application/pdf')


# return donate page
@app.route('/donate')
def donate():
    return render_template('donate.html')


# search function which will return a page contains information related to user's input
@app.route('/search')
def search():
    content = request.args['content']
    articles = article_service.search(content)
    comments = comment_service.search(content)
    if content == '':
        return 'Please input your searching content <a href="/">return</a>'
    return render_template('search.html', articles=articles, comments=comments)


# an author page which contains comments and articles upload by the user
@app.route('/user/<user_id>')
def user_page(user_id):
    user = user_service.find_by_id(user_id)
    articles = article_service.find_by_user(user)
    comments = comment_service.find_by_email(user.email)
    return render_template('user.html', articles=articles, user=user, comments=comments)


# this function will return a captcha image every time when it is requested.
@app.route('/captcha')
def captcha():
    def rndColor():
        return random.randint(32, 127), random.randint(32, 127), random.randint(32, 127)

    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    ret = ''
    width = 130
    height = 50
    im = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(im)
    for i in range(4):
        letter = random.choice(letters)
        ret += letter
        draw.text((5 + random.randint(-3, 3) + 23 * i, 5 + random.randint(-3, 3)),
                  text=letter, fill=rndColor(), font=ImageFont.truetype('arial.ttf', 40))
    for i in range(4):
        x1 = random.randint(0, width / 2)
        y1 = random.randint(0, height / 2)
        x2 = random.randint(0, width)
        y2 = random.randint(height / 2, height)
        draw.line(((x1, y1), (x2, y2)), fill='black', width=1)
    buf = BytesIO()
    im.save(buf, 'jpeg')
    buf_str = buf.getvalue()
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/gif'
    session['captcha'] = ret
    return response


if __name__ == '__main__':
    app.run(debug=True)
