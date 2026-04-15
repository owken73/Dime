from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import io
import csv
import os
from collections import defaultdict
from datetime import datetime

DB = 'dime.db'
app = Flask(__name__)

# 创建数据存储目录
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 交易类型对应的文件
FILES = {
    'expense': os.path.join(DATA_DIR, 'expenses.csv'),
    'income': os.path.join(DATA_DIR, 'income.csv'),
    'transfer': os.path.join(DATA_DIR, 'transfer.csv'),
    'balance': os.path.join(DATA_DIR, 'balance.csv'),
    'refund': os.path.join(DATA_DIR, 'refund.csv')
}

# 账户对应的文件
ACCOUNT_FILES = {
    'cash': os.path.join(DATA_DIR, 'accounts', 'cash.csv'),
    'wechat': os.path.join(DATA_DIR, 'accounts', 'wechat.csv'),
    'alipay': os.path.join(DATA_DIR, 'accounts', 'alipay.csv'),
    'unionpay': os.path.join(DATA_DIR, 'accounts', 'unionpay.csv'),
    'applepay': os.path.join(DATA_DIR, 'accounts', 'applepay.csv'),
    'bank': os.path.join(DATA_DIR, 'accounts', 'bank.csv')
}

# 创建账户目录
for account_file in ACCOUNT_FILES.values():
    account_dir = os.path.dirname(account_file)
    if not os.path.exists(account_dir):
        os.makedirs(account_dir)

# 初始化CSV文件
def init_csv_file(file_path, headers):
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

# 初始化所有文件
init_csv_file(FILES['expense'], ['date', 'category', 'sub_category', 'amount', 'description', 'account'])
init_csv_file(FILES['income'], ['date', 'category', 'sub_category', 'amount', 'description', 'account'])
init_csv_file(FILES['transfer'], ['date', 'from_account', 'to_account', 'amount', 'fee', 'description'])
init_csv_file(FILES['balance'], ['date', 'account', 'amount', 'description', 'type'])
init_csv_file(FILES['refund'], ['date', 'category', 'sub_category', 'amount', 'description', 'account'])

# 初始化类别使用次数文件
CATEGORY_USAGE_FILE = os.path.join(DATA_DIR, 'category_usage.csv')
init_csv_file(CATEGORY_USAGE_FILE, ['category', 'sub_category', 'count'])

# 初始化账户文件
for account_file in ACCOUNT_FILES.values():
    init_csv_file(account_file, ['date', 'type', 'amount', 'fee', 'description'])


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


# 更新类别使用次数
def update_category_usage(category, sub_category):
    # 读取现有使用次数
    usage_data = []
    if os.path.exists(CATEGORY_USAGE_FILE):
        with open(CATEGORY_USAGE_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # 跳过表头
            for row in reader:
                if len(row) >= 3:
                    usage_data.append(row)
    
    # 检查详细分类是否已存在
    found = False
    for row in usage_data:
        if row[0] == category and row[1] == sub_category:
            row[2] = str(int(row[2]) + 1)
            found = True
            break
    
    # 如果详细分类不存在，添加新记录
    if not found:
        usage_data.append([category, sub_category, '1'])
    
    # 检查主类别是否已存在（sub_category为空表示主类别）
    main_category_found = False
    for row in usage_data:
        if row[0] == category and row[1] == '':
            row[2] = str(int(row[2]) + 1)
            main_category_found = True
            break
    
    # 如果主类别不存在，添加新记录
    if not main_category_found:
        usage_data.append([category, '', '1'])
    
    # 写回文件
    with open(CATEGORY_USAGE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'sub_category', 'count'])
        for row in usage_data:
            writer.writerow(row)

# 保存交易到文件
def save_transaction_to_file(transaction_type, data):
    # 保存到交易类型文件
    if transaction_type in FILES:
        with open(FILES[transaction_type], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if transaction_type == 'expense' or transaction_type == 'income' or transaction_type == 'refund':
                # 解析类别和详细分类
                if 'category' in data:
                    category_parts = data['category'].split(' >> ')
                    main_category = category_parts[0] if len(category_parts) > 0 else ''
                    sub_category = category_parts[1] if len(category_parts) > 1 else ''
                    writer.writerow([
                        data['date'],
                        main_category,
                        sub_category,
                        data['amount'],
                        data.get('description', ''),
                        data.get('account', '')
                    ])
                    # 更新类别使用次数
                    update_category_usage(main_category, sub_category)
            elif transaction_type == 'transfer':
                writer.writerow([
                    data['date'],
                    data.get('from_account', ''),
                    data.get('to_account', ''),
                    data['amount'],
                    data.get('fee', 0),
                    data.get('description', '')
                ])
            elif transaction_type == 'balance':
                writer.writerow([
                    data['date'],
                    data.get('account', ''),
                    data['amount'],
                    data.get('description', ''),
                    data.get('type', '')
                ])

    # 保存到账户文件
    if transaction_type == 'expense' and 'account' in data and data['account'] in ACCOUNT_FILES:
        with open(ACCOUNT_FILES[data['account']], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['date'],
                'expense',
                -float(data['amount']),
                0,
                data.get('description', '')
            ])
    elif transaction_type == 'income' and 'account' in data and data['account'] in ACCOUNT_FILES:
        with open(ACCOUNT_FILES[data['account']], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['date'],
                'income',
                float(data['amount']),
                0,
                data.get('description', '')
            ])
    elif transaction_type == 'transfer':
        if 'from_account' in data and data['from_account'] in ACCOUNT_FILES:
            with open(ACCOUNT_FILES[data['from_account']], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['date'],
                    'transfer_out',
                    -float(data['amount']),
                    float(data.get('fee', 0)),
                    data.get('description', '')
                ])
        if 'to_account' in data and data['to_account'] in ACCOUNT_FILES:
            with open(ACCOUNT_FILES[data['to_account']], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['date'],
                    'transfer_in',
                    float(data['amount']),
                    0,
                    data.get('description', '')
                ])
    elif transaction_type == 'balance' and 'account' in data and data['account'] in ACCOUNT_FILES:
        with open(ACCOUNT_FILES[data['account']], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            amount = float(data['amount'])
            if data.get('type', '') == 'decrease':
                amount = -amount
            writer.writerow([
                data['date'],
                'balance_adjustment',
                amount,
                0,
                data.get('description', '')
            ])
    elif transaction_type == 'refund' and 'account' in data and data['account'] in ACCOUNT_FILES:
        with open(ACCOUNT_FILES[data['account']], 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['date'],
                'refund',
                float(data['amount']),
                0,
                data.get('description', '')
            ])


@app.route('/add', methods=['GET', 'POST'])
def add():
    """记一笔页面"""
    stats_open = request.cookies.get('statsMenuOpen', 'true')
    assets_open = request.cookies.get('assetsMenuOpen', 'true')

    if request.method == 'POST':
        # 获取表单数据
        amount = request.form.get('amount')
        category = request.form.get('category')
        date = request.form.get('date')
        description = request.form.get('description', '')
        account = request.form.get('account')
        transaction_type = request.form.get('type', 'expense')

        # 处理转账类型
        if transaction_type == 'transfer':
            from_account = request.form.get('from_account')
            to_account = request.form.get('to_account')
            fee = request.form.get('fee', '0')
            # 保存到文件
            save_transaction_to_file('transfer', {
                'date': date,
                'from_account': from_account,
                'to_account': to_account,
                'amount': amount,
                'fee': fee,
                'description': description
            })
        # 处理余额调整类型
        elif transaction_type == 'balance':
            balance_type = request.form.get('balance_type', 'increase')
            # 保存到文件
            save_transaction_to_file('balance', {
                'date': date,
                'account': account,
                'amount': amount,
                'description': description,
                'type': balance_type
            })
        # 处理其他类型
        else:
            # 处理"其他"分类时自定义的类型
            custom_category = request.form.get('custom_category')
            if custom_category:
                category = custom_category

            # 保存到文件
            save_transaction_to_file(transaction_type, {
                'date': date,
                'category': category,
                'amount': amount,
                'description': description,
                'account': account
            })

        # 插入数据库
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO expenses (date, category, amount, description)
            VALUES (?, ?, ?, ?)
        ''', (date, category, float(amount), description))
        conn.commit()
        conn.close()

        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {'status': 'success', 'message': '记账成功！'}
        else:
            return redirect(url_for('flow'))

    return render_template('add.html',
                           stats_menu_open=stats_open,
                           assets_menu_open=assets_open,
                           now=datetime.now)


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


@app.route('/api/transactions')
def get_transactions():
    """获取交易数据的 API"""
    import json
    
    # 从 CSV 文件中读取数据
    transactions = {
        'expenses': [],
        'income': [],
        'transfer': [],
        'refund': []
    }
    
    # 读取支出数据
    if os.path.exists(FILES['expense']):
        with open(FILES['expense'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['category']:
                    transactions['expenses'].append({
                        'date': row['date'],
                        'category': row['category'],
                        'sub_category': row['sub_category'],
                        'amount': float(row['amount']),
                        'description': row['description'],
                        'account': row['account']
                    })
    
    # 读取收入数据
    if os.path.exists(FILES['income']):
        with open(FILES['income'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['category']:
                    transactions['income'].append({
                        'date': row['date'],
                        'category': row['category'],
                        'sub_category': row['sub_category'],
                        'amount': float(row['amount']),
                        'description': row['description'],
                        'account': row['account']
                    })
    
    # 读取转账数据
    if os.path.exists(FILES['transfer']):
        with open(FILES['transfer'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                transactions['transfer'].append({
                    'date': row['date'],
                    'from_account': row['from_account'],
                    'to_account': row['to_account'],
                    'amount': float(row['amount']),
                    'fee': float(row['fee']),
                    'description': row['description']
                })
    
    # 读取退款数据
    if os.path.exists(FILES['refund']):
        with open(FILES['refund'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['category']:
                    transactions['refund'].append({
                        'date': row['date'],
                        'category': row['category'],
                        'sub_category': row['sub_category'],
                        'amount': float(row['amount']),
                        'description': row['description'],
                        'account': row['account']
                    })
    
    return json.dumps(transactions)


# ==================== 启动 ====================
if __name__ == '__main__':
    app.run(debug=True)
