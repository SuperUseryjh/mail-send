from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import os

app = Flask(__name__)

# Database configuration (same as Dash app)
DATABASE_FILE = '/app/users.db' # Path inside the Docker container
POSTFIX_HOST = os.environ.get('POSTFIX_HOST', 'postfix') # Hostname of the Postfix service in docker-compose
POSTFIX_PORT = int(os.environ.get('POSTFIX_PORT', 25))

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def get_user_by_api_key(api_key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE api_key = ?", (api_key,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_domain_by_user_and_name(user_id, domain_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, domain_name, is_verified FROM domains WHERE user_id = ? AND domain_name = ?", (user_id, domain_name))
    domain = cursor.fetchone()
    conn.close()
    return domain

@app.route('/send_email', methods=['POST'])
def send_email():
    # 1. API Key Authentication
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({"error": "API Key is missing"}), 401

    user = get_user_by_api_key(api_key)
    if not user:
        return jsonify({"error": "Invalid API Key"}), 401

    # 2. Parse Request Data
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    sender_email = data.get('sender_email')
    recipient_email = data.get('recipient_email')
    subject = data.get('subject')
    body = data.get('body')

    if not all([sender_email, recipient_email, subject, body]):
        return jsonify({"error": "Missing required email fields (sender_email, recipient_email, subject, body)"}), 400

    # Extract domain from sender_email
    sender_domain = sender_email.split('@')[-1]

    # 3. Sender Domain Validation
    domain_record = get_domain_by_user_and_name(user['id'], sender_domain)
    if not domain_record or not domain_record['is_verified']:
        return jsonify({"error": f"Domain '{sender_domain}' is not registered or not verified for this user."}), 403

    # 4. Send Email via Postfix
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(POSTFIX_HOST, POSTFIX_PORT) as server:
            # No authentication needed for local Postfix relay
            server.send_message(msg)

        return jsonify({"message": "Email sent successfully!"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)