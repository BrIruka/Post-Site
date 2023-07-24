import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = '3213912565674324'

def connect_db():
    conn = sqlite3.connect('forum.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, topic_on INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS topics (id INTEGER PRIMARY KEY, title TEXT, content TEXT, user_id INTEGER, date_time TEXT, FOREIGN KEY(user_id) REFERENCES users(id))')
    conn.commit()
    conn.close()

def is_authenticated():
    return 'user_id' in session

# Головна сторінка.
@app.route('/')
def index():
    # Отримуємо список тем з бази даних (ви можете розширити цю функцію для відображення контенту тем).
    conn = sqlite3.connect('forum.db')
    cursor = conn.cursor()
    cursor.execute('SELECT topics.id, topics.title, topics.content, topics.user_id, topics.date_time, users.username FROM topics INNER JOIN users ON topics.user_id = users.id')
    topics = cursor.fetchall()
    conn.close()

    return render_template('index.html', username=session.get('username'), topics=topics, dark_theme=session.get('dark_theme', False))

# Реєстрація нового користувача.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Перевіряємо, чи існує вже користувач з таким іменем в базі даних.
        conn = sqlite3.connect('forum.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username=?', (username,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            # Якщо користувач з таким іменем вже існує, попереджуємо про це.
            return render_template('register.html', message='Таке ім\'я користувача вже зайняте.')

        # Якщо користувача з таким іменем немає, додаємо його до бази даних.
        conn = sqlite3.connect('forum.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        # Після реєстрації перенаправляємо користувача на сторінку авторизації.
        return redirect(url_for('login'))

    return render_template('register.html', dark_theme=session.get('dark_theme', False))

# Вхід у свій профіль.
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Обробка форми входу.
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('forum.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))

    return render_template('login.html', dark_theme=session.get('dark_theme', False))

# Вихід зі свого профілю.
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Сторінка для створення нової теми.
@app.route('/create_topic', methods=['GET', 'POST'])
def create_topic():
    if not is_authenticated():
        return redirect(url_for('login'))

    conn = sqlite3.connect('forum.db')
    cursor = conn.cursor()
    cursor.execute('SELECT topic_on FROM users WHERE id=?', (session['user_id'],))
    topic_on = cursor.fetchone()
    conn.close()

    if not topic_on or topic_on[0] == 0:
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('forum.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO topics (title, content, user_id, date_time) VALUES (?, ?, ?, ?)', (title, content, session['user_id'], date_time))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('create_topic.html', dark_theme=session.get('dark_theme', False))


# Сторінка для видалення публікації.
@app.route('/delete_topic/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    if not is_authenticated():
        return redirect(url_for('login'))

    conn = sqlite3.connect('forum.db')
    cursor = conn.cursor()
    
    # Перевіряємо, чи існує публікація з вказаним ID та чи вона належить поточному користувачеві.
    cursor.execute('SELECT id FROM topics WHERE id=? AND user_id=?', (topic_id, session['user_id']))
    topic = cursor.fetchone()
    
    if not topic:
        # Якщо публікація не існує або не належить поточному користувачеві, перенаправляємо на головну сторінку.
        conn.close()
        return redirect(url_for('index'))

    # Видаляємо публікацію з бази даних.
    cursor.execute('DELETE FROM topics WHERE id=?', (topic_id,))
    conn.commit()
    conn.close()

    # Після видалення перенаправляємо на головну сторінку.
    return redirect(url_for('index'))



if __name__ == '__main__':
    connect_db()
    app.run(debug=True)
