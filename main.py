from flask import Flask, render_template, redirect, abort
from flask import request as r
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from data import db_session
from data.users import User
from data.requests import Request
from myIP import *
from forms import *
from waitress import serve


app = Flask(__name__)

app.config['SECRET_KEY'] = "Simeon's_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)


# главная страница
@app.route('/index')
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', form=form)


# функция для регистрации/авторизации пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            telephone_number=form.telephone_number.data,
            address={"city": form.city.data, "street": form.street.data, "building": form.building.data,
                     "flat": form.flat.data},
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# получаем для пользователя запросы, которые отправил он сам
def get_ingoing_requests(user):
    session = db_session.create_session()
    return session.query(Request).filter(Request.provider_id == user.id).all()


# получаем для пользователя запросы, которые он выполняет
def get_outgoing_requests(user):
    session = db_session.create_session()
    return session.query(Request).filter(Request.sender_id == user.id).all()


# флаг, отвечающий за показ входящих/исходящих запросов
flag_1 = True


@app.route("/profile")
def profile():
    global flag_1
    session = db_session.create_session()
    requests_users = []
    if flag_1:
        requests = get_outgoing_requests(current_user)
        for request in requests:
            user = session.query(User).filter(User.id == request.sender_id).first()
            requests_users.append((request, user))
    else:
        requests = get_ingoing_requests(current_user)
        for request in requests:
            user = session.query(User).filter(User.id == request.sender_id).first()
            requests_users.append((request, user))

    return render_template("profile.html", requests=requests_users, flag=flag_1)


# функции для добавления/редактирования/удаления запроса
@app.route('/request', methods=['GET', 'POST'])
@login_required
def add_request():
    form = RequestForm()
    if r.method == "GET":
        form.address.data = ", ".join(
            [current_user.address["city"], current_user.address["street"], current_user.address["building"],
             current_user.address["flat"]])
    if form.validate_on_submit():
        session = db_session.create_session()
        request = Request()
        request.name = form.name.data
        request.description = form.description.data
        request.is_active = form.is_active.data
        request.sender_id = current_user.id
        request.address = form.address.data
        session.add(request)
        session.commit()
        return redirect('/profile')
    return render_template('request_edit.html', title='Добавление запроса',
                           form=form)


# отображение интерактивной карты с запросами
@app.route('/map', methods=['GET', 'POST'])
def map_1():
    session = db_session.create_session()
    requests = []
    for request in session.query(Request).all():
        user = session.query(User).filter(User.id == request.sender_id).first()
        requests.append({"user": user.surname + " " + user.name,
                         "telephone": str(user.telephone_number),
                         "email": user.email,
                         "request": request
                         })
    if current_user.is_authenticated:
        outgoing_requests_ids = list(map(lambda x: x.id, get_outgoing_requests(current_user)))
        ingoing_requests_ids = list(map(lambda x: x.id, get_ingoing_requests(current_user)))
    else:
        outgoing_requests_ids = []
        ingoing_requests_ids = []
    coord = my_coord()
    return render_template("map_2.html", requests=requests, ingoing_requests_ids=ingoing_requests_ids,
                           outgoing_requests_ids=outgoing_requests_ids, coord=coord)


@app.route('/request/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_request(id):
    form = RequestForm()
    if r.method == "GET":
        session = db_session.create_session()
        request = session.query(Request).filter(Request.id == id,
                                                Request.sender_id == current_user.id).first()
        if request:
            form.name.data = request.name
            form.description.data = request.description
            form.is_active.data = request.is_active
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        request = session.query(Request).filter(Request.id == id,
                                                Request.sender_id == current_user.id).first()
        if request:
            request.name = form.name.data
            request.description = form.description.data
            request.is_active = form.is_active.data
            request.sender_id = current_user.id
            request.address = form.address.data
            session.commit()
            return redirect('/profile')
        else:
            abort(404)
    return render_template('request_edit.html', title='Редактирование новости', form=form)


@app.route('/request_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def request_delete(id):
    session = db_session.create_session()
    request = session.query(Request).filter(Request.id == id,
                                            Request.sender_id == current_user.id).first()
    if request:
        session.delete(request)
        session.commit()
    else:
        abort(404)
    return redirect('/profile')


# добавляем к пользователю входящий запрос
@app.route('/request_ingoing/<int:id>', methods=['GET', 'POST'])
@login_required
def add_ingoing_request(id):
    session = db_session.create_session()
    request = session.query(Request).filter(Request.id == id).first()
    request.provider_id = current_user.id
    session.commit()
    return redirect('/map')


# активируем неактивный запрос
@app.route('/request_activate/<int:id>')
def request_activate(id):
    session = db_session.create_session()
    request = session.query(Request).filter(Request.id == id).first()
    request.is_active = True
    session.commit()
    return redirect("/profile")


# деактивируем активный запрос
@app.route('/request_deactivate/<int:id>')
def request_deactivate(id):
    session = db_session.create_session()
    request = session.query(Request).filter(Request.id == id).first()
    request.is_active = False
    request.provider_id = None
    session.commit()
    return redirect("/profile")


# переключаемся на отображение входящих запросов
@app.route("/profile/switch/ingoing")
def profile_switch_ingoing():
    global flag_1
    flag_1 = False
    return redirect("/profile")


# переключаемся на отображение исходящих запросов
@app.route("/profile/switch/outgoing")
def profile_switch_outgoing():
    global flag_1
    flag_1 = True
    return redirect("/profile")


def main():
    # db_session.global_init('db/blogs.db')
    db_session.global_init("db/users_requests.sqlite")
    app.run(port=8000, host='127.0.0.1')


if __name__ == '__main__':
    main()