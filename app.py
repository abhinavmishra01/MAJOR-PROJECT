'''
This is the main file for the application. 
It contains the routes and views for the application.
'''

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from DATABASE import opendb, DB_URL
from DATABASE import User, Profile, Document
from db_helper import *
from validators import *
from logger import log
from werkzeug.utils import secure_filename
import os
from predictor import *
from tensorflow.keras.models import load_model

app = Flask(__name__)
app.secret_key  = '()*(#@!@#)'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def session_add(key, value):
    session[key] = value

def save_file(file):
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return path

def load_tf_model(path="model_casia_run1.h5"):
    return load_model(path)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg','tiff']



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    if not validate_email(email):
        flash('Invalid email', 'danger')
        return redirect(url_for('index'))
    if not validate_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('index'))
    db = opendb()
    user = db.query(User).filter_by(email=email).first()
    if user is not None and user.verify_password(password):
        session_add('user_id', user.id)
        session_add('user_name', user.name)
        session_add('user_email', user.email)
        session_add('isauth', True)
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password', 'danger')
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    db = opendb()
    if not validate_username(name):
        flash('Invalid username', 'danger')
        return redirect(url_for('index'))
    if not validate_email(email):
        flash('Invalid email', 'danger')
        return redirect(url_for('index'))
    if not validate_password(password):
        flash('Invalid password', 'danger')
        return redirect(url_for('index'))
    if password != cpassword:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('index'))
    if db.query(User).filter_by(email=email).first() is not None    :
        flash('Email already exists', 'danger')
        return redirect(url_for('index'))
    elif db.query(User).filter_by(name=name).first() is not None:
        flash('Username already exists', 'danger')
        return redirect(url_for('index'))
    else:
        db_save(User(name=name, email=email, password=password))
        flash('User registered successfully', 'success')
        return redirect(url_for('index'))
    
@app.route('/dashboard')
def dashboard():
    if session.get('isauth'):
        username = session.get('name')
        docs = opendb().query(Document).all()
        return render_template('dashboard.html',docs=docs,title=f'Home|{username}')
    else:
        return redirect(url_for('index'))

@app.route('/profile/add', methods=['POST'])
def add_profile():
    if session.get('isauth'):
        user_id = session.get('user_id')
        city = request.form.get('city')
        gender = request.form.get('gender')
        avatar = request.files.get('avatar')
        db = opendb()
        if not validate_city(city):
            flash('Invalid city', 'danger')
            return redirect(url_for('dashboard'))
        if not validate_avatar(avatar):
            flash('Invalid avatar file', 'danger')
            return redirect(url_for('dashboard'))
        if db.query(Profile).filter_by(user_id=user_id).first() is not None:
            flash('Profile already exists', 'danger')
            return redirect(url_for('view_profile'))
        else:
            db_save(Profile(user_id = user_id, city=city, gender=gender, avatar=save_file(avatar)))
            flash('Profile added successfully', 'success')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
        
@app.route('/profile/edit', methods=['POST'])
def edit_profile():
    if session.get('isauth'):
        profile = db_get_by_field(Profile, user_id=session.get('user_id'))
        if profile is not None:
            profile.city = request.form.get('city')
            profile.gender = request.form.get('gender')
            avatar = request.files.get('avatar')
            if avatar is not None:
                profile.avatar = save_file(avatar)
            db_save(profile)
            flash('Profile updated successfully', 'success')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))    

@app.route('/profile')
def view_profile():
    if session.get('isauth'):
        profile = db_get_by_field(Profile, user_id=session.get('user_id'))
        if profile is not None:
            return render_template('profile.html', profile=profile)
        else:
            flash(f'<a class="text-danger" href="#" data-bs-toggle="modal" data-bs-target="#profileModal">Create a profile</a>', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))
    

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    return render_template('upload.html')
    
@app.route('/upload/document/image', methods=['GET','POST'])
def upload_document_image():
    if 'isauth' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('dashboard'))
        if file and allowed_file(file.filename):
            path = save_file(file)
            session_add('last_document_image_path', path)
            flash('File uploaded successfully', 'success')
            db = opendb()
            user_id = session['user_id']
            document_image = Document(path=path, added_by=user_id)
            db.add(document_image)
            db.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file', 'danger')
            return redirect(url_for('dashboard'))

@app.route('/predict/<int:doc_id>/doc')
def predict(doc_id):
    doc = opendb().query(Document).filter_by(id=doc_id).first()
    model = load_tf_model()
    prediction,confidence = make_prediction(model, doc.path)
    session_add('last_prediction', prediction)
    session_add('ela', '/static/temp_ela.png')
    return render_template('predict.html',prediction=prediction,title='Prediction', confidence=confidence, doc=doc)

# delete
@app.route('/delete/<int:doc_id>')  
def delete_doc(doc_id):
    if session.get('isauth'):
        db = opendb()
        doc = db.query(Document).filter_by(id=doc_id).first()
        if doc is not None:
            db.delete(doc)
            db.commit()
            flash('Document deleted successfully', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Document not found', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login to continue', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
 