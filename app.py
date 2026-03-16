from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import io
import csv
from collections import defaultdict
from datetime import datetime

DB = 'dime.db'
app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
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


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页 - 重定向到统计页"""
    return redirect(url_for('stats_a'))


@app.route('/add')
def add():
    """记一笔页面"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('add.html',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/flow')
def flow():
    """流水页"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('flow.html',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/assets')
def assets():
    """资产页"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('assets.html',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/assets/a')
def assets_a():
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('assets_a.html',
                         page_title='资产总览',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/assets/b')
def assets_b():
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('assets_b.html',
                         page_title='账户明细',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/assets/c')
def assets_c():
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('assets_c.html',
                         page_title='资产趋势',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/stats')
def stats():
    """统计主页面 - 重定向到 stats/a"""
    return redirect(url_for('stats_a'))


@app.route('/stats/a')
def stats_a():
    """统计子页面A - 分类占比"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('stats_a.html',
                         page_title='分类占比',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/stats/b')
def stats_b():
    """统计子页面B - 近7天收支"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('stats_b.html',
                         page_title='近7天收支',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/stats/c')
def stats_c():
    """统计子页面C - 消费排行"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('stats_c.html',
                         page_title='消费排行',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/omg')
def omg():
    """OMG页"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('omg.html',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/profile')
def profile():
    """用户页"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('profile.html',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


@app.route('/settings')
def settings():
    """设置页"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')
    return render_template('settings.html',
                         stats_menu_open=stats_open,
                         assets_menu_open=assets_open)


# ==================== 启动 ====================
if __name__ == '__main__':
    app.run(debug=True)