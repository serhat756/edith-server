from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import time

app = Flask(__name__)

users_db = {}        # {email: {user_id, username, email, password_hash}}
active_tokens = {}   # {token: user_id}
messages_db = []     # [{id, sender_id, receiver_id, text, timestamp}]

@app.route('/')
def home():
    return jsonify({
        "status": "EDITH Auth & Chat Server Aktif",
        "users_count": len(users_db),
        "messages_count": len(messages_db)
    })

# 1. KAYIT
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        return jsonify({"status": "error", "message": "Tum alanlari doldurun."}), 400

    email = data['email'].strip().lower()
    username = data['username'].strip()
    password = data['password']

    if email in users_db:
        return jsonify({"status": "error", "message": "Bu e-posta zaten kayitli."}), 400

    new_id = str(uuid.uuid4())
    users_db[email] = {
        "user_id": new_id,
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password)
    }

    return jsonify({"status": "success", "message": "Kayit basarili. Giris yapabilirsiniz."}), 201

# 2. GİRİŞ
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"status": "error", "message": "E-posta ve sifre gereklidir."}), 400

    email = data['email'].strip().lower()
    password = data['password']

    user = users_db.get(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"status": "error", "message": "Hatali e-posta veya sifre."}), 401

    session_token = str(uuid.uuid4())
    active_tokens[session_token] = user['user_id']

    return jsonify({
        "status": "success",
        "message": "Giris basarili.",
        "token": session_token,
        "user": {
            "id": user['user_id'],
            "username": user['username'],
            "email": user['email']
        }
    }), 200

# 3. KULLANICI LİSTESİ (Sohbet Başlatmak İçin)
@app.route('/api/users', methods=['GET'])
def get_users():
    user_list = [
        {"id": u["user_id"], "username": u["username"], "email": u["email"]}
        for u in users_db.values()
    ]
    return jsonify({"status": "success", "users": user_list}), 200

# 4. MESAJ GÖNDERME
@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    text = data.get('text', '').strip()

    if not sender_id or not receiver_id or not text:
        return jsonify({"status": "error", "message": "Gecersiz mesaj parametreleri."}), 400

    msg = {
        "id": str(uuid.uuid4()),
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "text": text,
        "timestamp": int(time.time())
    }
    messages_db.append(msg)
    return jsonify({"status": "success", "message": msg}), 201

# 5. İKİ KULLANICI ARASINDAKİ MESAJLARI ÇEKME
@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')

    if not user1 or not user2:
        return jsonify({"status": "error", "message": "Kullanici ID'leri eksik."}), 400

    conversation = [
        m for m in messages_db
        if (m['sender_id'] == user1 and m['receiver_id'] == user2) or
           (m['sender_id'] == user2 and m['receiver_id'] == user1)
    ]
    return jsonify({"status": "success", "messages": conversation}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
