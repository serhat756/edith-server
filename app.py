from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime

app = Flask(__name__)

users = []
messages = []

@app.route('/')
def index():
    return jsonify({"status": "OK", "users": len(users), "messages": len(messages)})

@app.route('/api/register', methods=['POST'])
def register():
    d = request.get_json(force=True) or {}
    email = d.get('email', '').strip().lower()
    username = d.get('username', '').strip()
    password = d.get('password', '')

    if not email or not password:
        return jsonify({"status": "error", "message": "E-posta ve sifre zorunludur"}), 400

    if any(u['email'] == email for u in users):
        return jsonify({"status": "error", "message": "Bu e-posta zaten kayitli"}), 400

    uid = str(uuid.uuid4())
    users.append({
        "id": uid,
        "email": email,
        "username": username if username else email.split('@')[0],
        "password": generate_password_hash(password)
    })
    return jsonify({"status": "success", "id": uid}), 201

@app.route('/api/login', methods=['POST'])
def login():
    d = request.get_json(force=True) or {}
    email = d.get('email', '').strip().lower()
    password = d.get('password', '')

    user = next((u for u in users if u['email'] == email), None)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"status": "error", "message": "Hatali e-posta veya sifre"}), 401

    return jsonify({
        "status": "success",
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]}
    }), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({"users": [{"id": u["id"], "username": u["username"], "email": u["email"]} for u in users]}), 200

@app.route('/api/send_message', methods=['POST'])
def send_message():
    d = request.get_json(force=True) or {}
    s = d.get('sender_id')
    r = d.get('receiver_id')
    t = d.get('text')
    client_time = d.get('time')
    
    if not s or not r or not t:
        return jsonify({"status": "error", "message": "Eksik parametre"}), 400

    msg = {
        "id": str(uuid.uuid4()),
        "sender_id": s,
        "receiver_id": r,
        "text": t,
        "time": client_time if client_time else datetime.datetime.now().strftime("%H:%M"),
        "status": "delivered"
    }
    messages.append(msg)
    return jsonify({"status": "success", "message": msg}), 201

@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    u1 = request.args.get('user1')
    u2 = request.args.get('user2')
    
    if not u1 or not u2:
        return jsonify({"messages": []}), 200

    for m in messages:
        if m.get('sender_id') == u2 and m.get('receiver_id') == u1:
            m['status'] = 'read'

    conv = [
        m for m in messages 
        if (m.get('sender_id') == u1 and m.get('receiver_id') == u2) or 
           (m.get('sender_id') == u2 and m.get('receiver_id') == u1)
    ]
    return jsonify({"messages": conv}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
