from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)

users_db = {}
active_tokens = {}

@app.route('/')
def home():
    return jsonify({"status": "EDITH Auth & Chat Server Aktif", "users_count": len(users_db)})

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

    users_db[email] = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password)
    }

    return jsonify({"status": "success", "message": "Kayit basarili. Giris yapabilirsiniz."}), 201

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
