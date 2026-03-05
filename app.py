from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import io
import csv
from collections import defaultdict

DB='dime.db'
app = Flask(__name__)

#数据库连接
def get_db_connection():

    conn=sqlite3.connect(DB)
    conn.row_factory=sqlite3.Row
    return conn

@app.before_request
def ensure_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT
    );''')
    conn.commit()
    conn.close()