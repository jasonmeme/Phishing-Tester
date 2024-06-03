# api/app.py

from flask import Flask, request, render_template, url_for, redirect, flash
import smtplib
from email.mime.text import MIMEText
import uuid
import psycopg2
import os
import logging
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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

        subject = 'Test Email'
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Account Information</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px; }}
                .email-container {{ max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                .email-header, .email-footer {{ text-align: center; margin-bottom: 20px; }}
                .email-body {{ margin-bottom: 20px; }}
                .btn {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 5px; font-size: 16px; }}
                .btn:hover {{ background-color: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Verify Your Account</h1>
                </div>
                <div class="email-body">
                    <p>Dear {email},</p>
                    <p>We noticed unusual login activity on your account, and for your security, we need you to verify your account information. Please take a moment to review your recent activity and ensure that your account information is up to date.</p>
                    <p>To verify your account, please click the button below:</p>
                    <p><a href="{tracking_url}" class="btn">Verify Your Account</a></p>
                    <p>If you did not attempt to log in, please disregard this email, and we apologize for any inconvenience.</p>
                    <p>Best regards,</p>
                    <p><br>Webex<br><a href="mailto:help.webex.cisco@gmail.com">help.webex.cisco@gmail.com</a></p>
                </div>
                <div class="email-footer">
                    <p>&copy; 2024 Webex. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg = MIMEText(body, 'html')
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
    except Exception as e:
        logging.error(f"Error in send_phishing_email: {e}")
        return 'Internal Server Error', 500

@app.route('/send_phishing_emails', methods=['POST'])
def send_phishing_emails():
    try:
        init_db()  # Initialize database
        file = request.files['csv-file']
        if not file:
            flash('No file uploaded', 'error')
            return redirect(url_for('index'))
        
        file_data = file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_data)
        emails = [row[0] for row in csv_reader]

        for email in emails:
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

            subject = 'Test Email'
            body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Account Information</title>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px; }}
                    .email-container {{ max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                    .email-header, .email-footer {{ text-align: center; margin-bottom: 20px; }}
                    .email-body {{ margin-bottom: 20px; }}
                    .btn {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 5px; font-size: 16px; }}
                    .btn:hover {{ background-color: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1>Verify Your Account</h1>
                    </div>
                    <div class="email-body">
                        <p>Dear {email},</p>
                        <p>We noticed unusual login activity on your account, and for your security, we need you to verify your account information. Please take a moment to review your recent activity and ensure that your account information is up to date.</p>
                        <p>To verify your account, please click the button below:</p>
                        <p><a href="{tracking_url}" class="btn">Verify Your Account</a></p>
                        <p>If you did not attempt to log in, please disregard this email, and we apologize for any inconvenience.</p>
                        <p>Best regards,</p>
                        <p><br>Webex<br><a href="mailto:help.webex.cisco@gmail.com">help.webex.cisco@gmail.com</a></p>
                    </div>
                    <div class="email-footer">
                        <p>&copy; 2024 Webex. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg = MIMEText(body, 'html')
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
        
        flash('Emails sent successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error in send_phishing_emails: {e}")
        flash('Failed to send emails', 'error')
        return redirect(url_for('index'))

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