from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from flask_login import LoginManager, current_user, logout_user, login_user, login_required
from wtforms import TextField, TextAreaField, validators, PasswordField, StringField, SubmitField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_wtf import FlaskForm

import os
from sqlalchemy.orm import sessionmaker
from create_db import *

app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'

@app.teardown_request
def remove_session(ex=None):
    session.remove()
    
@login.user_loader
def load(id):
	users=session.query(User)
	return users.get(int(id))

 
class LoginForm(FlaskForm):
	username = StringField('Username', validators=[validators.required()])
	password = PasswordField('Password', validators=[validators.required()])
	submit = SubmitField('Login')
	remember_me=BooleanField('Remember me')
    
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    remember_me=BooleanField('Remember me')

    def validate_username(self, username):
    	users=session.query(User)
        user = users.filter_by(username=username.data).first()
        if user is not None:
        	flash('This user name exists in the system. Please use a different username.')
        	raise ValidationError('Please use a different username.')

    def validate_email(self, email):
    	users = session.query(User)  
        user = users.filter_by(email=email.data).first()
        if user is not None:
        	flash('This user email exists in the system.')
        	raise ValidationError('Please use a different email address.')
             
class NoteForm(FlaskForm):
    note = TextField('Note:', validators=[validators.required()])
    category = TextField('Category:', validators=[validators.required(), validators.Length(min=4, max=100)])
    submit = SubmitField('Save')

 
@app.route('/')
def home():
	return render_template("index.html", title="My Notes")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
    	print "Validated"
        user = User(username=form.username.data, password=form.password.data, email=form.email.data)
        session.add(user)
        session.commit()
        flash('Congratulations, you are now a registered user!')
        print "Registered"
        login_user(user, remember=form.remember_me.data)
        print "Logged in"
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)

@app.route('/notes', methods=['GET'])
@login_required
def notes():
	notes = session.query(Note)
	user_notes=notes.filter_by(user_id=current_user.get_id()).all()
	return render_template("notes.html", title="All Notes", notes=user_notes)
  
@app.route("/add_note", methods=['GET', 'POST'])
def add_note():
    form = NoteForm(request.form)
 
    print form.errors
    if request.method == 'POST':
        note=request.form['note']
        category=request.form['category']
        print note, " ", category
 
        if form.validate():
        	Session = sessionmaker(bind=engine)
        	s = Session()
        	added_note = Note(current_user.get_id(), note,category)
        	s.add(added_note)
        	s.commit()
        	flash('Thanks for note ' + note)
        	return notes()
        else:
            flash('Error: All the form fields are required. ')
 
    return render_template('note.html', form=form, title="Adding Notes")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
    	print "Validated"
    	users = session.query(User)  
        user=users.filter_by(username=form.username.data).first()
        print user
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('notes'))
    return render_template('login.html', title='Sign In', form=form)
     
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))
 
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)