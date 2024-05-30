# api/app.py

from flask import Flask, request, render_template, url_for
import smtplib
from email.mime.text import MIMEText
import uuid
import sqlite3
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_phishing_email', methods=['POST'])
def send_phishing_email():
    email = request.form['email']
    unique_id = str(uuid.uuid4())
    tracking_url = url_for('track_click', id=unique_id, _external=True)
    
    # Shorten the URL using TinyURL API
    response = requests.get(f'http://tinyurl.com/api-create.php?url={tracking_url}')
    shortened_url = response.text
    
    # Store tracking information in the database
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('''INSERT INTO clicks (id, email, clicked) VALUES (?, ?, ?)''', (unique_id, email, False))
    conn.commit()
    conn.close()

    subject = 'Test Phishing Email'
    body = f'This is a simulated phishing email. Do not click on any links.\nTracking URL: {shortened_url}'
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'bobsterthebob55@gmail.com'  # Replace with your email
    msg['To'] = email
    
    # Update with your SMTP server configuration
    # Update with your Gmail configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'bobsterthebob55@gmail.com'
    smtp_password = 'ttva tajs reka yklc'
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_user, smtp_password)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
    
    return 'Phishing email sent!'

@app.route('/track/<id>')
def track_click(id):
    # Update database to indicate the link was clicked
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('''UPDATE clicks SET clicked = ? WHERE id = ?''', (True, id))
    conn.commit()
    conn.close()
    
    return 'Link clicked!'

@app.route('/results')
def view_results():
    conn = sqlite3.connect('phishing.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM clicks''')
    rows = c.fetchall()
    conn.close()
    return render_template('results.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
