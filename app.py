import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, IMAGES, configure_uploads
from datetime import datetime

app = Flask(__name__)
app.secret_key = "Kelvin2026yyyy@"

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orphanage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOADED_PHOTOS_DEST'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# --- UPLOAD SETUP ---
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10))
    photo_filename = db.Column(db.String(200))  # Stores filename
    story = db.Column(db.Text)
    school_grade = db.Column(db.String(50))
    location = db.Column(db.String(200))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50))
    message = db.Column(db.Text)
    date_donated = db.Column(db.DateTime, default=datetime.utcnow)

class BuildingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    amount_raised = db.Column(db.Float, default=0.0)
    target_amount = db.Column(db.Float, default=100000.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    embed_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

# --- CREATE TABLES ---
with app.app_context():
    db.create_all()
    if not BuildingProgress.query.first():
        db.session.add(BuildingProgress(description="Build permanent orphanage home", target_amount=100000.0))
        db.session.commit()
    if not Video.query.first():
        db.session.add(Video(title="Welcome to KM Orphanage", embed_url="https://www.youtube.com/embed/dQw4w9WgXcQ", description="A tour of our home"))
        db.session.commit()

# --- PUBLIC PAGES ---
@app.route('/')
def home():
    children = Child.query.order_by(Child.date_added.desc()).limit(6).all()
    videos = Video.query.all()
    total_donations = db.session.query(db.func.sum(Donor.amount)).scalar() or 0.0
    progress = BuildingProgress.query.first()
    donor_count = Donor.query.count()
    return render_template('index.html', 
        children=children, 
        videos=videos,
        total=total_donations, 
        progress=progress,
        donor_count=donor_count)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/gallery')
def gallery():
    children = Child.query.all()
    return render_template('gallery.html', children=children)

@app.route('/sponsor')
def sponsor():
    return render_template('sponsor.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        donor = Donor(
            name=request.form['name'],
            email=request.form['email'],
            amount=float(request.form['amount']),
            method=request.form['method'],
            message=request.form['message']
        )
        db.session.add(donor)
        
        progress = BuildingProgress.query.first()
        progress.amount_raised += float(request.form['amount'])
        progress.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash(f"Thank you {donor.name}! Your donation of K{donor.amount} via {donor.method} is changing lives.", "success")
        return redirect(url_for('home'))
    return render_template('donate.html')

# --- ADMIN PANEL (SECURE) ---
ADMIN_PASSWORD = "Kelvin2026yyyy@"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            children = Child.query.all()
            donors = Donor.query.all()
            progress = BuildingProgress.query.first()
            videos = Video.query.all()
            return render_template('admin.html', children=children, donors=donors, progress=progress, videos=videos)
        else:
            flash("Wrong password! Access denied.", "danger")
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/admin/add_child', methods=['GET', 'POST'])
def add_child():
    if request.method == 'POST':
        # Handle photo upload
        if 'photo' in request.files and request.files['photo'].filename != '':
            filename = photos.save(request.files['photo'])
        else:
            filename = 'default.jpg'
        
        child = Child(
            name=request.form['name'],
            age=int(request.form['age']),
            gender=request.form['gender'],
            photo_filename=filename,
            story=request.form['story'],
            school_grade=request.form['school_grade'],
            location=request.form['location']
        )
        db.session.add(child)
        db.session.commit()
        flash(f"Child {child.name} added successfully!", "success")
        return redirect(url_for('admin'))
    return render_template('add_child.html')

@app.route('/admin/delete_child/<int:id>')
def delete_child(id):
    child = Child.query.get_or_404(id)
    db.session.delete(child)
    db.session.commit()
    flash(f"Removed {child.name}", "warning")
    return redirect(url_for('admin'))

@app.route('/admin/add_video', methods=['POST'])
def add_video():
    video = Video(
        title=request.form['title'],
        embed_url=request.form['embed_url'],
        description=request.form['description']
    )
    db.session.add(video)
    db.session.commit()
    flash("Video added successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/admin/delete_video/<int:id>')
def delete_video(id):
    video = Video.query.get_or_404(id)
    db.session.delete(video)
    db.session.commit()
    flash("Video removed", "warning")
    return redirect(url_for('admin'))

# --- STATIC FILES (Uploaded images) ---
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)

if __name__ == '__main__':
    app.run(debug=True)