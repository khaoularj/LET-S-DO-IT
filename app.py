from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
app.config['SECRET_KEY'] = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)



app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "log_in"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class TaskList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('ToDo', backref='list', lazy=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    lists = db.relationship('TaskList', backref='user', lazy=True)
    tasks = db.relationship('ToDo', backref='user', lazy=True)

class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('task_list.id'), nullable=False)

class SignUp(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    email = EmailField(validators=[InputRequired(), Email(), Length(min=8, max=120)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('This email is already registered! Please sign up with another one.')

class LogIn(FlaskForm):
    email = EmailField(validators=[InputRequired(), Email(message='Invalid email address'), Length(min=8, max=120)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Log In")

@app.route('/auth/login', methods=['GET', 'POST'])
def log_in():
    form = LogIn()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('dashboard/log_in.html', form=form)

"""
@app.route('/auth/signup', methods=['GET', 'POST'])
def sign_up():
    form = SignUp()
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('log_in'))
    return render_template('dashboard/sign_up2.html', form=form)
"""
@app.route('/auth/signup', methods=['GET', 'POST'])
def sign_up():
    form = SignUp()
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('log_in'))
    return render_template('dashboard/sign_up.html', form=form)



@app.route('/auth/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    return redirect(url_for('log_in'))

@app.route('/')
def index():
    return render_template('dashboard/landing_page.html')

@app.route('/change_background_color', methods=['POST'])
def change_background_color():
    if request.method == 'POST':
        color = request.form.get('color')
        session['background_color'] = color
        return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    lists = TaskList.query.filter_by(user_id=current_user.id).all()
    total = len([task for task_list in lists for task in task_list.tasks])
    completed_tasks = len([task for task_list in lists for task in task_list.tasks if task.complete])
    uncompleted_tasks = total - completed_tasks
    return render_template('dashboard/dashboard.html', lists=lists, total=total, completed_tasks=completed_tasks, uncompleted_tasks=uncompleted_tasks)

@app.route('/add_list', methods=['POST'])
@login_required
def add_list():
    list_name = request.form.get('list_name')
    if list_name:
        new_list = TaskList(name=list_name, user_id=current_user.id)
        db.session.add(new_list)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_task/<int:list_id>', methods=['POST'])
@login_required
def add_task(list_id):
    task_description = request.form.get('task_description')
    if task_description:
        new_task = ToDo(description=task_description, user_id=current_user.id, list_id=list_id)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = ToDo.query.get(task_id)
    if task and task.user_id == current_user.id:
        task.complete = not task.complete
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = ToDo.query.get(task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_list/<int:list_id>', methods=['POST'])
@login_required
def delete_list(list_id):
    task_list = TaskList.query.get(list_id)
    if task_list and task_list.user_id == current_user.id:
        for task in task_list.tasks:
            db.session.delete(task)
        db.session.delete(task_list)
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
