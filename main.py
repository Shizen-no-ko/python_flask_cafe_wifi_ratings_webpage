from flask import Flask, flash, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DecimalField, BooleanField, RadioField
from wtforms.validators import DataRequired, URL
from datetime import datetime
from random import shuffle
from dotenv import load_dotenv
import os

load_dotenv()

# For year in copyright notice
now = datetime.now()
current_year = now.strftime("%Y")

app = Flask(__name__)
Bootstrap(app)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Wtforms
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


db = SQLAlchemy(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)


# Form for adding new cafes
class CafeForm(FlaskForm):
    name = StringField('Cafe name', validators=[DataRequired()])
    location = StringField('Location of cafe', validators=[DataRequired()])
    map_url = StringField('Cafe Location on Google Maps (URL)', validators=[DataRequired(), URL()])
    image_url = StringField('Image of the cafe (URL)', validators=[DataRequired(), URL()])
    seats = StringField('How many seats?', validators=[DataRequired()])
    coffee_price = DecimalField('How much does a cup of coffee cost? £', validators=[DataRequired()])
    has_wifi = SelectField('Does the cafe have wifi?', choices=[('True', 'Yes'), ('False', 'No')])
    has_sockets = SelectField('Does the cafe have charging points?', choices=[('True', 'Yes'), ('False', 'No')])
    has_toilet = SelectField('Does the cafe have a toilet?', choices=[('True', 'Yes'), ('False', 'No')])
    can_take_calls = SelectField('Does the cafe take calls for customers?', choices=[('True', 'Yes'), ('False', 'No')])
    submit = SubmitField('Submit')


# Form for filtering cafes in database
class FilterForm(FlaskForm):
    location = SelectField('Select Location', choices=[('All Locations', 'All Locations')] + sorted(
        list(set([(value.title(), value.title()) for (value,) in (db.session.query(Cafe.location).all())]))))
    has_wifi = BooleanField('Cafe with WiFi', false_values=None)
    has_toilet = BooleanField('Cafe has a Toilet', false_values=None)
    has_sockets = BooleanField('Cafe has Charging Points', false_values=None)
    can_take_calls = BooleanField('Cafe can Take Calls', false_values=None)
    # Workaround to get coffee price label displaying
    # https: // stackoverflow.com / questions / 27705968 / flask - wtform - radiofield - label - does - not -render
    coffee_price = RadioField(label='Maximum Coffee Price. Less than:',
                              choices=[('2', '£2.00'), ('2.50', '£2.50'), ('3.0', '£3.00'), ('20', 'No Limit')],
                              default='20')
    reset = SubmitField('Reset')
    submit = SubmitField('Filter')


def coerce(value):
    # To compensate for Boolean coercion problems
    if value == "True":
        return True
    elif value == "False":
        return False


@app.route("/", methods=['POST', 'GET'])
def home():
    form = FilterForm()
    cafe_list = []
    if form.validate_on_submit():
        if form.reset.data:
            return redirect(url_for('home'))
        if form.submit.data:
            cafe_list = []
            all_cafes = Cafe.query.all()
            for cafe in all_cafes:
                # Render only if there is a match
                match = True
                # Various checks against a match from form
                if (form.has_wifi.data and not cafe.has_wifi):
                    match = False
                if (form.has_toilet.data and not cafe.has_toilet):
                    match = False
                if (form.has_sockets.data and not cafe.has_sockets):
                    match = False
                if (form.can_take_calls.data and not cafe.can_take_calls):
                    match = False
                if form.location.data != "All Locations" and cafe.location != form.location.data:
                    match = False
                if float(form.coffee_price.data) < float(cafe.coffee_price.split("£")[1]):
                    match = False
                    # If cafe still matches all criteria, add it to render list
                if match:
                    cafe_list.append(cafe)
            return render_template("index.html", current_year=current_year, cafe_list=cafe_list, form=form)
    all_cafes = Cafe.query.all()
    for cafe in all_cafes:
        cafe_list.append(cafe)
        # ensures cafes render in random order
    shuffle(cafe_list)
    return render_template("index.html", current_year=current_year, cafe_list=cafe_list, form=form, is_home=True)


@app.route("/add", methods=["POST", "GET"])
def add():
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data.strip(),
            map_url=form.map_url.data,
            img_url=form.image_url.data,
            location=form.location.data.strip(),
            seats=form.seats.data,
            has_toilet=coerce(form.has_toilet.data),
            has_wifi=coerce(form.has_wifi.data),
            has_sockets=coerce(form.has_sockets.data),
            can_take_calls=coerce(form.can_take_calls.data),
            # To compensate for user not entering 2 decimal places
            coffee_price=f"£{str(format(form.coffee_price.data, '.2f'))}")
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add.html", form=form, current_year=current_year)


@app.route("/delete/<id>", methods=["GET"])
def delete(id):
    cafe_to_delete = Cafe.query.get(id)
    deleted_name = cafe_to_delete.name
    db.session.delete(cafe_to_delete)
    db.session.commit()
    flash(f'{deleted_name} was successfully deleted.')
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)

