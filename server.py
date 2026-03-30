import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, send_from_directory, request

DB_PATH = 'reports.db'
FINGERPRINT_KEY = os.environ.get('FINGERPRINT_KEY', 'dev-secret-change-in-production')

app = Flask(__name__, static_folder='site', static_url_path='')


def device_fingerprint(req):
    """
    Produces a stable token to loosely identify the same device across multiple
    submissions, without storing anything on the client or identifying individuals.

    The token is an HMAC-SHA256 hash of three signals:
      - IP /24 prefix (first three octets): stable within a home network or
        carrier, but coarse enough that the exact IP is not recoverable.
      - User-Agent: includes phone model class, OS and browser version. Changes
        only on software updates, so stable over days to weeks.
      - Accept-Language: the user's language/locale setting, very stable.

    Using HMAC with a server-side secret means the hash is one-way: even with
    full database access, the original IP, UA, or language cannot be reconstructed.
    The token is intentionally fuzzy — two people with the same phone on the same
    carrier subnet could collide — but for the purpose of loosely grouping reports
    by device over time, that is an acceptable tradeoff.
    """
    ip = req.remote_addr or ''
    parts = ip.split('.')
    if len(parts) == 4:
        ip_prefix = '.'.join(parts[:3])
    else:
        ip_prefix = ':'.join(ip.split(':')[:4])  # IPv6: first 4 groups

    ua = req.headers.get('User-Agent', '')
    lang = req.headers.get('Accept-Language', '')

    raw = f"{ip_prefix}|{ua}|{lang}"
    return hmac.new(FINGERPRINT_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            container_oc     INTEGER  NOT NULL,
            condition        INTEGER  NOT NULL,
            received_at_utc  TEXT     NOT NULL,
            device_token     TEXT     NOT NULL
        )
    ''')
    db.commit()
    db.close()
    print("Database ready.")


@app.route('/')
def index():
    return send_from_directory('site', 'index.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    container_oc = int(data['container_oc'])
    condition = int(data['condition'])
    device_token = device_fingerprint(request)
    received_at_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    db = sqlite3.connect(DB_PATH)
    db.execute(
        'INSERT INTO reports (container_oc, condition, received_at_utc, device_token) VALUES (?, ?, ?, ?)',
        (container_oc, condition, received_at_utc, device_token)
    )
    db.commit()
    db.close()

    print(f"Received: container {container_oc}, condition: {condition}, device: {device_token[:8]}…")
    return '', 204


if 'FINGERPRINT_KEY' in os.environ:
    print("FINGERPRINT_KEY loaded from environment.")
else:
    print("WARNING: FINGERPRINT_KEY not set. Using insecure default — set the env var before deploying.")

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
