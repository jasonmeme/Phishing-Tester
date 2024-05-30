# api/app.py

from flask import Flask, request, render_template, url_for, stream_with_context, Response
import smtplib
from email.mime.text import MIMEText
import uuid
import psycopg2
import os
import logging
import csv

app = Flask(__name__)

# Database connection parameters
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id UUID PRIMARY KEY,
            email TEXT NOT NULL,
            clicked BOOLEAN NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    init_db()  # Initialize database
    return render_template('index.html')

@app.route('/send_phishing_email', methods=['POST'])
def send_phishing_email():
    try:
        init_db()  # Initialize database
        email = request.form['email']
        unique_id = str(uuid.uuid4())
        tracking_url = url_for('track_click', id=unique_id, _external=True)
        
        # Store tracking information in the database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO clicks (id, email, clicked) VALUES (%s, %s, %s)
        ''', (unique_id, email, False))
        conn.commit()
        cur.close()
        conn.close()

        subject = 'Test Phishing Email'
        body = f'This is a simulated phishing email. Do not click on any links.\nTracking URL: {tracking_url}'
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = os.getenv('SMTP_USER')  # Use environment variable
        msg['To'] = email
        
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(smtp_user, smtp_password)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        
        return 'Phishing email sent!'
    except Exception as e:
        logging.error(f"Error in send_phishing_email: {e}")
        return 'Internal Server Error', 500

@app.route('/send_phishing_emails', methods=['POST'])
def send_phishing_emails():
    @stream_with_context
    def generate():
        file = request.files['csv-file']
        if not file:
            yield "0"
            return
        file_data = file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_data)
        emails = [row[0] for row in csv_reader]

        total_emails = len(emails)
        for i, email in enumerate(emails):
            try:
                unique_id = str(uuid.uuid4())
                tracking_url = url_for('track_click', id=unique_id, _external=True)
                
                # Store tracking information in the database
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO clicks (id, email, clicked) VALUES (%s, %s, %s)
                ''', (unique_id, email, False))
                conn.commit()
                cur.close()
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
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(msg['From'], [msg['To']], msg.as_string())
                
                progress = int((i + 1) / total_emails * 100)
                yield str(progress)
            except Exception as e:
                logging.error(f"Error in send_phishing_emails for {email}: {e}")
                yield "0"

    return Response(generate(), mimetype='text/plain')

@app.route('/track/<id>')
def track_click(id):
    try:
        init_db()  # Initialize database
        # Update database to indicate the link was clicked
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            UPDATE clicks SET clicked = TRUE WHERE id = %s
        ''', (id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return 'Link clicked!'
    except Exception as e:
        logging.error(f"Error in track_click: {e}")
        return 'Internal Server Error', 500

@app.route('/results')
def view_results():
    try:
        init_db()  # Initialize database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM clicks')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('results.html', rows=rows)
    except Exception as e:
        logging.error(f"Error in view_results: {e}")
        return 'Internal Server Error', 500

if __name__ == '__main__':
    app.run(debug=True)
