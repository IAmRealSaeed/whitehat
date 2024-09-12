from datetime import datetime

from flask import Flask, request, jsonify, redirect, url_for, session, render_template, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from cryptography.fernet import Fernet
import os
from flask import Flask, request, render_template, session, redirect, url_for
import sqlite3
import time
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import jdatetime
app = Flask(__name__, static_url_path='/static')
import os

secret_key = os.urandom(24)  # Generates a 24-byte (192-bit) random key
app.secret_key = secret_key  # Required to use sessions

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

data = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)  # Assuming User.get(user_id) fetches the user from the database


# Route to serve index.html as default page
# def serve_index():
#     # return send_from_directory(os.path.join(app.root_path, 'templates'), 'index.html')
#     return render_template('index.html')


# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = user[1]  # Store username in session
            login_user(User(user[0]))
            return redirect(url_for('one'))
        else:
            return 'Invalid credentials', 403

    return send_from_directory(os.path.join(app.root_path, 'templates'), 'login.html')


# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already exists', 400
        finally:
            conn.close()

    return send_from_directory(os.path.join(app.root_path, 'templates'), 'register.html')


# Route to log out
@app.route('/logout')
def logout():
    session.pop('user', None)
    logout_user()
    return redirect(url_for('login'))


# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER NOT NULL,
            correct_answer TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            number INTEGER NOT NULL,
            submission_time INTEGER
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# # Route to serve index.html
# @app.route('/')
# def serve_index():
#     return render_template('index.html')

# Route to check the answer
@app.route('/check_answer', methods=['POST'])
def check_answer():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    number1 = request.form['number']
    user_answer = request.form['answer']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    number = data.get(number1)
    # Get the correct answer from the database
    cursor.execute('SELECT correct_answer FROM answer WHERE number = ?', (number,))
    result = cursor.fetchone()

    if result:
        correct_answer = result[0]
        if user_answer == correct_answer:
            # If the answer is correct, log the time in UNIX format
            submission_time = int(time.time())

            # Check if the user already has a submission record for this number
            cursor.execute('SELECT * FROM submit WHERE username = ? AND number = ?', (username, number))
            existing_submission = cursor.fetchone()

            if existing_submission:
                # Update the existing submission
                cursor.execute('UPDATE submit SET submission_time = ? WHERE username = ? AND number = ?',
                               (submission_time, username, number))
            else:
                # Insert a new submission
                cursor.execute('INSERT INTO submit (username, number, submission_time) VALUES (?, ?, ?)',
                               (username, number, submission_time))

            conn.commit()
            conn.close()

            return redirect(url_for(number1))

        else:
            conn.close()
            return render_template('index.html', message='The answer is not correct.', question=number1)
    else:
        conn.close()
        return render_template('index.html', message='Invalid question number.')

@app.route('/')
@app.route('/one', methods=['GET'])
@login_required

def one():
    current_endpoint = request.endpoint
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    number1 = request.endpoint

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    number = data.get(number1)

    cursor.execute('SELECT * FROM submit WHERE username = ? AND number = ?', (username, number))
    existing_submission = cursor.fetchone()
    if not existing_submission:
        return render_template('index.html', question=current_endpoint)
    # Convert timestamp to Gregorian datetime
    gregorian_date = datetime.fromtimestamp(existing_submission[3])

    # Convert Gregorian datetime to Jalali date
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)

    # Format Jalali date and time
    formatted_jalali = jalali_date.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('index.html', question=current_endpoint, timestamp=formatted_jalali)


@app.route('/two', methods=['GET'])
def two():
    current_endpoint = request.endpoint
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    number1 = request.endpoint

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    number = data.get(number1)

    cursor.execute('SELECT * FROM submit WHERE username = ? AND number = ?', (username, number))
    existing_submission = cursor.fetchone()
    if not existing_submission:
        return render_template('index.html', question=current_endpoint)
    # Convert timestamp to Gregorian datetime
    gregorian_date = datetime.fromtimestamp(existing_submission[3])

    # Convert Gregorian datetime to Jalali date
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)

    # Format Jalali date and time
    formatted_jalali = jalali_date.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('index.html', question=current_endpoint, timestamp=formatted_jalali)


@app.route('/three', methods=['GET'])
def three():
    current_endpoint = request.endpoint
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    number1 = request.endpoint

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    number = data.get(number1)

    cursor.execute('SELECT * FROM submit WHERE username = ? AND number = ?', (username, number))
    existing_submission = cursor.fetchone()
    if not existing_submission:
        return render_template('index.html', question=current_endpoint)
    # Convert timestamp to Gregorian datetime
    gregorian_date = datetime.fromtimestamp(existing_submission[3])

    # Convert Gregorian datetime to Jalali date
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)

    # Format Jalali date and time
    formatted_jalali = jalali_date.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('index.html', question=current_endpoint, timestamp=formatted_jalali)


@app.route('/four', methods=['GET'])
def four():
    current_endpoint = request.endpoint
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    number1 = request.endpoint

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    number = data.get(number1)

    cursor.execute('SELECT * FROM submit WHERE username = ? AND number = ?', (username, number))
    existing_submission = cursor.fetchone()
    if not existing_submission:
        return render_template('index.html', question=current_endpoint)
    # Convert timestamp to Gregorian datetime
    gregorian_date = datetime.fromtimestamp(existing_submission[3])

    # Convert Gregorian datetime to Jalali date
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)

    # Format Jalali date and time
    formatted_jalali = jalali_date.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('index.html', question=current_endpoint, timestamp=formatted_jalali)


@app.route('/five', methods=['GET'])
def five():
    current_endpoint = request.endpoint
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    number1 = request.endpoint

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    number = data.get(number1)

    cursor.execute('SELECT * FROM submit WHERE username = ? AND number = ?', (username, number))
    existing_submission = cursor.fetchone()
    if not existing_submission:
        return render_template('index.html', question=current_endpoint)
    # Convert timestamp to Gregorian datetime
    gregorian_date = datetime.fromtimestamp(existing_submission[3])

    # Convert Gregorian datetime to Jalali date
    jalali_date = jdatetime.datetime.fromgregorian(datetime=gregorian_date)

    # Format Jalali date and time
    formatted_jalali = jalali_date.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('index.html', question=current_endpoint, timestamp=formatted_jalali)


if __name__ == '__main__':
    app.run(debug=True)
