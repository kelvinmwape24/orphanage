 
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kelvin2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orphanage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10))
    photo_url = db.Column(db.String(200))
    story = db.Column(db.Text)
    school_grade = db.Column(db.String(50))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text)
    date_donated = db.Column(db.DateTime, default=datetime.utcnow)

class BuildingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    amount_raised = db.Column(db.Float, default=0.0)
    target_amount = db.Column(db.Float, default=50000.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

# --- CREATE TABLES ---
with app.app_context():
    db.create_all()
    if not BuildingProgress.query.first():
        db.session.add(BuildingProgress(description="Build new orphanage dormitory", target_amount=50000.0))
        db.session.commit()

# --- PUBLIC PAGES ---
@app.route('/')
def home():
    children = Child.query.order_by(Child.date_added.desc()).limit(6).all()
    total_donations = db.session.query(db.func.sum(Donor.amount)).scalar() or 0.0
    progress = BuildingProgress.query.first()
    donor_count = Donor.query.count()
    return render_template('index.html', 
        children=children, 
        total=total_donations, 
        progress=progress,
        donor_count=donor_count)

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
            message=request.form['message']
        )
        db.session.add(donor)
        
        progress = BuildingProgress.query.first()
        progress.amount_raised += float(request.form['amount'])
        progress.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash(f"Thank you {donor.name}! Your donation of K{donor.amount} is changing lives.", "success")
        return redirect(url_for('home'))
    return render_template('donate.html')

# --- ADMIN PANEL ---
ADMIN_PASSWORD = "kelvin2026"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            children = Child.query.all()
            donors = Donor.query.all()
            progress = BuildingProgress.query.first()
            return render_template('admin.html', children=children, donors=donors, progress=progress)
        else:
            flash("Wrong password!", "danger")
            return redirect(url_for('admin'))
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Admin Login</title></head>
    <body style="font-family:Arial;text-align:center;padding-top:100px;">
        <h2>Orphanage Admin Login</h2>
        <form method="post">
            <input type="password" name="password" placeholder="Enter admin password" required>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    '''

@app.route('/admin/add_child', methods=['GET', 'POST'])
def add_child():
    if request.method == 'POST':
        child = Child(
            name=request.form['name'],
            age=int(request.form['age']),
            gender=request.form['gender'],
            photo_url=request.form['photo_url'],
            story=request.form['story'],
            school_grade=request.form['school_grade']
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

if __name__ == '__main__':
    app.run(debug=True)