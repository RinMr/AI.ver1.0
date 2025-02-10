from flask import Flask, json, flash, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from pytz import timezone
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from functools import wraps
import pickle
import time
import base64
import uuid
import logging

app = Flask(__name__)
app.secret_key = 'bouhurin'
app.jinja_env.globals.update(json=json, max=max, zip=zip)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

history_log = []
old_history_log = []

JST = timezone('Asia/Tokyo')

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    labels = db.Column(db.Text, nullable=False)
    probs = db.Column(db.Text, nullable=False)
    emotions = db.Column(db.Text, nullable=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(JST))

with app.app_context():
    db.create_all()

app.jinja_env.globals.update(zip=zip)
@app.template_filter('zip')
def zip_filter(a, b):
    return zip(a, b)

animal_label_encoder = None
emotion_label_encoder = None

def load_models():
    global animal_label_encoder, emotion_label_encoder

    animal_model = load_model('models/model.h5')
    with open('models/class_indices.pkl', 'rb') as f:
        animal_label_encoder = pickle.load(f)

    animal_index_to_label = {v: k for k, v in animal_label_encoder.items()}

    emotion_model = load_model('models/emotion_model.h5')
    with open('models/emotion_class_indices.pkl', 'rb') as f:
        emotion_label_encoder = pickle.load(f)

    emotion_index_to_label = {v: k for k, v in emotion_label_encoder.items()}

    return animal_model, animal_index_to_label, emotion_model, emotion_index_to_label

animal_model, animal_index_to_label, emotion_model, emotion_index_to_label = load_models()

def preprocess_image_for_animal_model(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    img = cv2.resize(img, (96, 96))
    img = img / 255.0
    return np.expand_dims(img, axis=0)

def preprocess_image_for_emotion_model(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (224, 224))
    img = img / 255.0
    return np.expand_dims(img, axis=0)

animal_label_jp_dict = {
    "cat": "ネコ",
    "dog": "イヌ",
    "lion": "ライオン",
    "monkey": "サル",
    "wolf": "オオカミ"
}

emotion_label_jp_dict = {
    "cat_angry": "ネコ-怒る",
    "cat_happy": "ネコ-楽しい",
    "cat_sad": "ネコ-悲しい",
    "dog_angry": "イヌ-怒る",
    "dog_happy": "イヌ-楽しい",
    "dog_sad": "イヌ-悲しい",
    "lion_angry": "ライオン-怒る",
    "lion_happy": "ライオン-楽しい",
    "lion_sad": "ライオン-悲しい",
    "monkey_angry": "サル-怒る",
    "monkey_happy": "サル-楽しい",
    "monkey_sad": "サル-悲しい",
    "wolf_angry": "オオカミ-怒る",
    "wolf_happy": "オオカミ-楽しい",
    "wolf_sad": "オオカミ-悲しい"
}

def translate_label_to_japanese(label, translation_dict):
    return translation_dict.get(label, label)

def predict_image(image_path, user_id, unique_filename):
    global history_log, old_history_log

    processed_image_animal = preprocess_image_for_animal_model(image_path)
    processed_image_emotion = preprocess_image_for_emotion_model(image_path)

    animal_predictions = animal_model.predict(processed_image_animal)[0]
    animal_probs = (animal_predictions * 100).tolist()
    animal_indices = range(len(animal_predictions))
    index_to_label = [label for label, index in sorted(animal_label_encoder.items(), key=lambda item: item[1])]
    animal_labels = [translate_label_to_japanese(label, animal_label_jp_dict) for label in index_to_label]
    animal_index = np.argmax(animal_predictions)
    animal_label = translate_label_to_japanese(index_to_label[animal_index], animal_label_jp_dict)
    animal_confidence = animal_predictions[animal_index] * 100

    emotion_predictions = emotion_model.predict(processed_image_emotion)[0]
    emotion_probs = (emotion_predictions * 100).tolist()
    emotion_indices = range(len(emotion_predictions))
    emotion_labels = [translate_label_to_japanese(emotion_index_to_label.get(i, "Unknown"), emotion_label_jp_dict) for i in emotion_indices]
    emotion_details = dict(zip(emotion_labels, emotion_probs))

    if animal_confidence < 50:
        message = "識別できませんでした"
    else:
        message = f"これは{animal_label}です"

    new_image = Image(
        user_id=user_id,
        filename=unique_filename, 
        labels=json.dumps(animal_labels),
        probs=json.dumps(animal_probs),
        emotions=json.dumps(emotion_details),
        message=message,
    )
    db.session.add(new_image)
    db.session.commit()

    return animal_label, animal_confidence, message, emotion_details, animal_labels, animal_probs

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            session['just_logged_in'] = True
            return redirect(url_for('home'))
        else:
            error_message = "名前またはパスワードが正しくありません。"
            return render_template('login.html', error=error_message)
        
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(image_path)

        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        animal_label, animal_confidence, message, emotion_details, animal_labels, animal_probs = predict_image(image_path, user_id, unique_filename)

        _, img_encoded = cv2.imencode('.png', cv2.imread(image_path))
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')

        predictions = list(zip(animal_labels, animal_probs))
        timeout_url = url_for('timeout') 
        return render_template(
            'decision.html',
            message=message,
            image=f'<img src="data:image/png;base64,{img_base64}" alt="予測画像" />',
            emotion_details=emotion_details,
            predictions=predictions,
            top_label=animal_label,
            timeout_url=timeout_url,
            animal_confidence=animal_confidence,
        )
    return render_template('home.html', history=history_log, timestamp=int(time.time()), zip=zip)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            error_message = "ユーザー名が既に使用されています"
            return redirect(url_for('register', error=error_message))
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/home')
@login_required
def home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('login'))
    
    timeout_url = url_for('timeout')
    just_logged_in = session.pop('just_logged_in', False)
    
    return render_template('home.html', 
        user=user, 
        history=history_log, 
        timestamp=int(time.time()), 
        zip=zip, 
        timeout_url=timeout_url,
        just_logged_in=just_logged_in)


@app.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    user_id = session.get('user_id')

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            
            if data.get('delete_all'):
                images = Image.query.filter_by(user_id=user_id).all()
                if images:
                    for image in images:
                        db.session.delete(image)
                    db.session.commit()
                    return jsonify({"success": True, "message": "すべての履歴が削除されました。"}), 200
                return jsonify({"success": False, "message": "削除する履歴がありませんでした。"}), 404

        image_id = request.form.get('image_id')
        if image_id:
            image = Image.query.filter_by(id=image_id, user_id=user_id).first()
            if image:
                db.session.delete(image)
                db.session.commit()
                flash('履歴が削除されました。')
            else:
                flash('履歴が見つかりませんでした。')
        return redirect(url_for('history'))

    user_images = Image.query.filter_by(user_id=user_id).order_by(Image.timestamp.desc()).all()
    timeout_url = url_for('timeout')
    return render_template('history.html', history=user_images, timestamp=int(time.time()), timeout_url=timeout_url)

@app.route('/old_history', methods=['GET', 'POST'])
@login_required
def old_history():
    user_id = session.get('user_id')

    user_images = Image.query.filter_by(user_id=user_id).order_by(Image.timestamp.desc()).all()
    old_history_images = user_images[3:]
    unique_dates = sorted(set(image.timestamp.date().isoformat() for image in user_images), reverse=True)
    date_grouped_images = {
        date: [img for img in old_history_images if img.timestamp.date().isoformat() == date]
        for date in unique_dates
    }

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            image_id = data.get('image_id')
            if image_id:
                image = Image.query.filter_by(id=image_id, user_id=user_id).first()
                if image:
                    try:
                        db.session.delete(image)
                        db.session.commit()
                        return jsonify({"success": True, "message": "選択された履歴が削除されました。"}), 200
                    except Exception as e:
                        db.session.rollback()
                        return jsonify({"success": False, "message": str(e)}), 500
                else:
                    return jsonify({"success": False, "message": "指定された履歴が見つかりませんでした。"}), 404
            return jsonify({"success": False, "message": "image_idがありません。"}), 400

        image_id = request.form.get('image_id')
        if image_id:
            image = Image.query.filter_by(id=image_id, user_id=user_id).first()
            if image:
                db.session.delete(image)
                db.session.commit()
                flash('選択された履歴が削除されました。')
            else:
                flash('指定された履歴が見つかりませんでした。')
        return redirect(url_for('old_history'))

    timeout_url = url_for('timeout')
    return render_template(
        'old_history.html', 
        old_history=old_history_images, 
        unique_dates=unique_dates, 
        date_grouped_images=date_grouped_images, 
        timestamp=int(time.time()), 
        timeout_url=timeout_url
    )

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.before_request
def check_session_timeout():
    session.permanent = True
    if 'user_id' in session:
        session.modified = True
    else:
        if request.endpoint not in ['login', 'register', 'static', 'timeout']:
            flash('一定時間操作がされなかったため、タイムアウトしました。')
            return redirect(url_for('timeout'))

@app.route('/timeout')
def timeout():
    session.clear()
    return render_template('timeout.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
    app.run(debug=False, host='0.0.0.0', port=5000)