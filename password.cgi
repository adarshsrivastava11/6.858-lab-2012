#!/usr/bin/env python

from wsgiref.handlers import CGIHandler
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return """
username: root<br>
password: 6858"""

if __name__ == "__main__":
    CGIHandler().run(app)
