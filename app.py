import os
from datetime import timedelta

from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/thoth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['WHOOSH_BASE'] = 'db/whoosh/base'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024


if __name__ == "__main__":
    app.run(debug=True)
