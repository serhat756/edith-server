from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime

app = Flask(__name__)

users_db = {}
active_tokens = {}
messages_db = []

@app.route('/')
def home():
    return jsonify({
        "status": "EDITH Auth & Chat Server Aktif",
        "users_count": len(users_db),
        "messages_count": len(messages_db)
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not email or not username or not password:
        return jsonify({"status": "error", "message": "Tum alanlari doldurun."}), 400

    if email in users_db:
        return jsonify({"status": "error", "message": "Bu e-posta zaten kayitli."}), 400

    new_id = str(uuid.uuid4())
    users_db[email] = {
        "user_id": new_id,
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password)
    }

    return jsonify({"status": "success", "message": "Kayit basarili."}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = users_db.get(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"status": "error", "message": "Hatali e-posta veya sifre."}), 401

    session_token = str(uuid.uuid4())
    active_tokens[session_token] = user['user_id']

    return jsonify({
        "status": "success",
        "token": session_token,
        "user": {
            "id": user['user_id'],
            "username": user['username'],
            "email": user['email']
        }
    }), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    user_list = [
        {"id": u["user_id"], "username": u["username"], "email": u["email"]}
        for u in users_db.values()
    ]
    return jsonify({"status": "success", "users": user_list}), 200

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.get_json() or {}
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    text = data.get('text', '').strip()

    if not sender_id or not receiver_id or not text:
        return jsonify({"status": "error", "message": "Gecersiz mesaj."}), 400

    now = datetime.datetime.now()
    msg = {
        "id": str(uuid.uuid4()),
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "text": text,
        "time": now.strftime("%H:%M"),
        "status": "delivered"  # sent, delivered, read
    }
    messages_db.append(msg)
    return jsonify({"status": "success", "message": msg}), 201

@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')

    if not user1 or not user2:
        return jsonify({"status": "error", "message": "ID eksik."}), 400

    # user2'nin user1'e attığı mesajları 'okundu' (read) yap
    for m in messages_db:
        if m['sender_id'] == user2 and m['receiver_id'] == user1:
            m['status'] = 'read'

    conversation = [
        m for m in messages_db
        if (m['sender_id'] == user1 and m['receiver_id'] == user2) or
           (m['sender_id'] == user2 and m['receiver_id'] == user1)
    ]
    return jsonify({"status": "success", "messages": conversation}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
