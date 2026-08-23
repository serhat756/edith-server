from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
import datetime

app = Flask(__name__)
DB_FILE = "edith.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    username TEXT,
                    password TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    sender_id TEXT,
                    receiver_id TEXT,
                    text TEXT,
                    time TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    u_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    m_count = c.fetchone()[0]
    conn.close()
    return jsonify({
        "status": "EDITH Auth & Chat Server Aktif (SQLite)",
        "users_count": u_count,
        "messages_count": m_count
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not email or not username or not password:
        return jsonify({"status": "error", "message": "Tum alanlari doldurun."}), 400

    new_id = str(uuid.uuid4())
    pw_hash = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO users (id, email, username, password) VALUES (?, ?, ?, ?)",
                  (new_id, email, username, pw_hash))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Kayit basarili."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Bu e-posta zaten kayitli."}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, email, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if not user or not check_password_hash(user[3], password):
        return jsonify({"status": "error", "message": "Hatali e-posta veya sifre."}), 401

    return jsonify({
        "status": "success",
        "user": {
            "id": user[0],
            "username": user[1],
            "email": user[2]
        }
    }), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, email FROM users")
    rows = c.fetchall()
    conn.close()

    users = [{"id": r[0], "username": r[1], "email": r[2]} for r in rows]
    return jsonify({"status": "success", "users": users}), 200

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.get_json() or {}
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    text = data.get('text', '').strip()

    if not sender_id or not receiver_id or not text:
        return jsonify({"status": "error", "message": "Gecersiz mesaj verisi."}), 400

    msg_id = str(uuid.uuid4())
    msg_time = datetime.datetime.now().strftime("%H:%M")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (id, sender_id, receiver_id, text, time, status) VALUES (?, ?, ?, ?, ?, ?)",
              (msg_id, sender_id, receiver_id, text, msg_time, "delivered"))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": {
            "id": msg_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "text": text,
            "time": msg_time,
            "status": "delivered"
        }
    }), 201

@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')

    if not user1 or not user2:
        return jsonify({"status": "error", "message": "ID eksik."}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Karşıdan bana gelen mesajları okundu yap
    c.execute("UPDATE messages SET status = 'read' WHERE sender_id = ? AND receiver_id = ?", (user2, user1))
    conn.commit()

    # İki kişi arasındaki tüm mesajları sıralı çek
    c.execute("""SELECT id, sender_id, receiver_id, text, time, status 
                 FROM messages 
                 WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
                 ORDER BY created_at ASC""", (user1, user2, user2, user1))
    rows = c.fetchall()
    conn.close()

    messages = [
        {"id": r[0], "sender_id": r[1], "receiver_id": r[2], "text": r[3], "time": r[4], "status": r[5]}
        for r in rows
    ]
    return jsonify({"status": "success", "messages": messages}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
