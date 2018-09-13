from flask import render_template, Flask, url_for, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
# import pymysql

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
from app import models,views