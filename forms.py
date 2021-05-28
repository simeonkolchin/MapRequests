from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField, TelField


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    telephone_number = TelField("Номер телефона", validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    street = StringField('Улица', validators=[DataRequired()])
    building = StringField('Дом', validators=[DataRequired()])
    flat = StringField('Квартира')
    about = TextAreaField('Немного о себе')
    submit = SubmitField('Зарегистрироваться')


class RequestForm(FlaskForm):
    name = StringField('Заголовок', validators=[DataRequired()])
    description = TextAreaField("Содержание")
    address = TextAreaField("Адрес", validators=[DataRequired()])
    is_active = BooleanField("Активен/неактивен")
    submit = SubmitField('Применить')
