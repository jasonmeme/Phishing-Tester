# api/app.py

from flask import Flask, request, render_template, url_for
import smtplib
from email.mime.text import MIMEText
import uuid
import sqlite3
import requests
import os

app = Flask(__name__)

DATABASE = os.path.join(os.getcwd(), 'phishing.db')

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clicks
                    (id TEXT PRIMARY KEY, email TEXT, clicked BOOLEAN)''')
        conn.commit()
        conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_phishing_email', methods=['POST'])
def send_phishing_email():
    email = request.form['email']
    unique_id = str(uuid.uuid4())
    tracking_url = url_for('track_click', id=unique_id, _external=True)
    
    # Store tracking information in the database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO clicks (id, email, clicked) VALUES (?, ?, ?)''', (unique_id, email, False))
    conn.commit()
    conn.close()

    subject = 'Test Phishing Email'
    body = f'This is a simulated phishing email. Do not click on any links.\nTracking URL: {tracking_url}'
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv('SMTP_USER')  # Use environment variable
    msg['To'] = email
    
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_user, smtp_password)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
    
    return 'Phishing email sent!'

@app.route('/track/<id>')
def track_click(id):
    # Update database to indicate the link was clicked
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''UPDATE clicks SET clicked = ? WHERE id = ?''', (True, id))
    conn.commit()
    conn.close()
    
    return 'Link clicked!'

@app.route('/results')
def view_results():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT * FROM clicks''')
    rows = c.fetchall()
    conn.close()
    return render_template('results.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
