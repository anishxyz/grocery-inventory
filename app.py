from flask import (
    Flask, render_template, redirect, url_for, request, flash, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required, UserMixin, current_user
)
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, IntegerField, FloatField
)
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import csv
import emoji

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


# Forms
class LoginForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=4, max=150)]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login ' + emoji.emojize(':key:'))


class RegisterForm(FlaskForm):
    username = StringField(
        'Username', validators=[DataRequired(), Length(min=4, max=150)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=4)]
    )
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register ' + emoji.emojize(':check_mark_button:'))


class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Submit ' + emoji.emojize(':shopping_cart:'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.before_first_request
def create_tables():
    db.create_all()


@app.route('/')
@login_required
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(emoji.emojize('Logged in successfully! :thumbs_up:'), 'success')
            return redirect(url_for('index'))
        flash(emoji.emojize('Invalid username or password. :warning:'), 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(emoji.emojize('You have been logged out. :wave:'), 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(
            username=form.username.data
        ).first()
        if existing_user:
            flash(emoji.emojize('Username already exists. :no_entry_sign:'), 'danger')
            return redirect(url_for('register'))
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(emoji.emojize('Registration successful! Please log in. :smile:'), 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/item/add', methods=['GET', 'POST'])
@login_required
def add_item():
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            quantity=form.quantity.data,
            price=form.price.data
        )
        db.session.add(item)
        db.session.commit()
        flash(emoji.emojize('Item added successfully! :tada:'), 'success')
        return redirect(url_for('index'))
    return render_template('item_form.html', form=form, action='Add')


@app.route('/item/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data
        item.quantity = form.quantity.data
        item.price = form.price.data
        db.session.commit()
        flash(emoji.emojize('Item updated successfully! :pencil2:'), 'success')
        return redirect(url_for('index'))
    return render_template('item_form.html', form=form, action='Edit')


@app.route('/item/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(emoji.emojize('Item deleted successfully. :wastebasket:'), 'success')
    return redirect(url_for('index'))


@app.route('/export', methods=['GET'])
@login_required
def export_items():
    items = Item.query.all()
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Quantity', 'Price'])
    for item in items:
        writer.writerow([item.id, item.name, item.quantity, item.price])
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        attachment_filename='inventory.csv',
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)
