from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spendit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Модели ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    quiz_done = db.Column(db.Boolean, default=False)
    interests = db.Column(db.String(200), default='')
    income = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='user')
    purchases = db.relationship('Purchase', backref='user', lazy=True)
    complaints = db.relationship('Complaint', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Integer, nullable=True)
    desc = db.Column(db.Text)
    details = db.Column(db.Text)
    image = db.Column(db.String(300), default='https://via.placeholder.com/300x200?text=New')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(200))
    price = db.Column(db.Integer)
    date = db.Column(db.String(50))

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer)
    product_name = db.Column(db.String(200))
    text = db.Column(db.Text)
    date = db.Column(db.String(50))
    reply = db.Column(db.Text, nullable=True)
    replied_by = db.Column(db.String(80), nullable=True)

# --- Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Инициализация БД ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin',
            quiz_done=True
        )
        db.session.add(admin)
        db.session.commit()

    if Product.query.count() == 0:
        products = [
            Product(name="Беспроводные наушники", category="Электроника", price=3500, original_price=5000,
                    desc="Отличный звук, активное шумоподавление.", details="Глубокий бас, до 30 часов работы, Bluetooth 5.2, кейс для зарядки."),
            Product(name="Набор Lego Technic", category="Хобби", price=8900, original_price=10990,
                    desc="Собери суперкар или экскаватор — 1500+ деталей.", details="Детализированная модель с подвижными элементами."),
            Product(name="Умная колонка", category="Электроника", price=7500,
                    desc="Яндекс.Станция Миди с Алисой.", details="Голосовой помощник, управление умным домом, отличный звук."),
            Product(name="Абонемент в спортзал (месяц)", category="Спорт", price=2500,
                    desc="Безлимит на все зоны и групповые занятия.", details="Тренажёры, бассейн, сауна. Без ограничений по времени."),
            Product(name="Кожаный кошелёк", category="Аксессуары", price=4200, original_price=5500,
                    desc="Ручная работа, натуральная кожа.", details="Отделения для карт и купюр, RFID-защита."),
            Product(name="Билет на концерт", category="Развлечения", price=5500,
                    desc="Популярная группа в вашем городе.", details="Место в партере, живой звук."),
            Product(name="Курс по Python", category="Образование", price=19900, original_price=24900,
                    desc="Продвинутое программирование от практиков.", details="60 часов видео, проекты в портфолио."),
            Product(name="Самокат электро", category="Транспорт", price=28000,
                    desc="До 25 км/ч, запас хода 30 км.", details="Мощный мотор 350 Вт, дисковые тормоза."),
            Product(name="Фотосессия в студии", category="Услуги", price=6000,
                    desc="2 часа съёмки + 30 обработанных фото.", details="Профессиональный фотограф."),
            Product(name="Робот-пылесос", category="Дом", price=18000, original_price=22000,
                    desc="Сухая и влажная уборка, построение карты.", details="Лидар-навигация, управление со смартфона."),
            Product(name="Сертификат в спа", category="Услуги", price=8000,
                    desc="Массаж, обёртывание и хамам.", details="Подарочный сертификат на 3 часа."),
            Product(name="Настольная игра", category="Развлечения", price=2900, original_price=3500,
                    desc="Колонизаторы. Для компании от 3 человек.", details="Стратегия, развивающая мышление."),
            Product(name="Кроссовки брендовые", category="Одежда", price=12000,
                    desc="Последняя коллекция, удобная колодка.", details="Натуральная кожа, амортизация."),
            Product(name="Годовая подписка на книги", category="Образование", price=4500,
                    desc="Букмейт или ЛитРес — читай без ограничений.", details="Доступ к 1 000 000 книг."),
            Product(name="Скейтборд", category="Спорт", price=5600, original_price=6900,
                    desc="Классический круизер из канадского клёна.", details="Длина 27 дюймов, алюминиевая подвеска."),
            Product(name="Блендер мощный", category="Дом", price=7000,
                    desc="Смузи, супы-пюре, колка льда.", details="Мощность 1200 Вт, чаша 2 л."),
            Product(name="Наручные часы", category="Аксессуары", price=15000, original_price=18900,
                    desc="Японский механизм, водозащита 100 м.", details="Сапфировое стекло, кожаный ремешок."),
            Product(name="Прыжок с парашютом", category="Развлечения", price=11000,
                    desc="Тандем-прыжок с инструктором, видео.", details="Высота 4000 метров."),
            Product(name="Электрический чайник с терморегуляцией", category="Дом", price=4200, original_price=4900,
                    desc="Поддержание температуры, 1.7 л.", details="Нагрев до 100°C, автоотключение."),
            Product(name="Путешествие на выходные", category="Путешествия", price=25000,
                    desc="Тур в соседний город, отель 3*, трансфер.", details="Два дня, экскурсии, питание включено.")
        ]
        db.session.add_all(products)
        db.session.commit()

# --- Контекстный процессор (глобальные переменные для шаблонов) ---
@app.context_processor
def inject_globals():
    categories = sorted({p.category for p in Product.query.all()})
    return dict(categories=categories)

# --- Персональная сортировка ---
def personalized_sort(offers, user):
    income = user.income
    interests = user.interests.split(',') if user.interests else []
    rec_budget = (income / 15 + income / 30) / 2 if income > 0 else 0
    def score(product):
        in_interest = 1 if product.category in interests else 0
        price_diff = abs(product.price - rec_budget)
        price_bonus = max(0, 100 - price_diff / (rec_budget / 2 + 1) * 100) if rec_budget > 0 else 0
        return in_interest * 1000 + price_bonus - price_diff * 0.1
    return sorted(offers, key=score, reverse=True)

# --- Аутентификация ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()
        if not username or not password:
            flash('Логин и пароль обязательны.')
        elif password != confirm:
            flash('Пароли не совпадают.')
        elif User.query.filter_by(username=username).first():
            flash('Пользователь с таким логином уже существует.')
        else:
            user = User(username=username, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Давайте заполним анкету.')
            login_user(user)
            return redirect(url_for('quiz'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Пользователь не найден.')
        elif not check_password_hash(user.password, password):
            flash('Неверный пароль.')
        else:
            login_user(user)
            flash(f'Добро пожаловать, {username}!')
            if not user.quiz_done and user.role not in ('admin', 'subadmin'):
                return redirect(url_for('quiz'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.')
    return redirect(url_for('login'))

# --- Анкета ---
@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    if current_user.quiz_done:
        flash('Анкета уже пройдена.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        interests = ','.join(request.form.getlist('interests'))
        income_str = request.form.get('income', '').strip()
        if not income_str:
            flash('Пожалуйста, укажите ваш примерный доход.')
            return render_template('quiz.html', categories=sorted({p.category for p in Product.query.all()}))
        try:
            income = int(income_str)
            if income <= 0:
                raise ValueError
        except ValueError:
            flash('Введите корректный положительный доход.')
            return render_template('quiz.html', categories=sorted({p.category for p in Product.query.all()}))
        current_user.interests = interests
        current_user.income = income
        current_user.quiz_done = True
        db.session.commit()
        flash('Анкета заполнена!')
        return redirect(url_for('index'))
    cats = sorted({p.category for p in Product.query.all()})
    return render_template('quiz.html', categories=cats)

# --- Главная ---
@app.route('/')
@login_required
def index():
    budget = request.args.get('budget', '', type=int)
    selected_categories = request.args.getlist('category')
    sort_option = request.args.get('sort', 'price_asc')
    products = Product.query.all()
    personalized = False
    rec_budget = None
    if current_user.quiz_done and not budget and not selected_categories:
        personalized = True
        if current_user.income > 0:
            rec_budget = int((current_user.income / 15 + current_user.income / 30) / 2)
        products = personalized_sort(products, current_user)
    else:
        if budget and budget > 0:
            products = [p for p in products if p.price <= budget]
        if selected_categories:
            products = [p for p in products if p.category in selected_categories]
        if sort_option == 'price_asc':
            products.sort(key=lambda x: x.price)
        elif sort_option == 'price_desc':
            products.sort(key=lambda x: x.price, reverse=True)
        elif sort_option == 'name_asc':
            products.sort(key=lambda x: x.name.lower())
        elif sort_option == 'name_desc':
            products.sort(key=lambda x: x.name.lower(), reverse=True)
    return render_template('index.html',
                           offers=products,
                           budget=budget if budget else '',
                           selected_categories=selected_categories,
                           sort_option=sort_option,
                           personalized=personalized,
                           rec_budget=rec_budget)

# --- Страница товара ---
@app.route('/product/<int:product_id>')
@login_required
def product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Товар не найден.')
        return redirect(url_for('index'))
    return render_template('product.html', offer=product)

# --- Покупка ---
@app.route('/buy/<int:product_id>', methods=['POST'])
@login_required
def buy(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Товар не найден'}), 404
    purchase = Purchase(
        user_id=current_user.id,
        product_id=product_id,
        product_name=product.name,
        price=product.price,
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(purchase)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Покупка совершена!'})

# --- Жалоба ---
@app.route('/product/<int:product_id>/complain', methods=['POST'])
@login_required
def complain(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Товар не найден.')
        return redirect(url_for('index'))
    text = request.form.get('complaint_text', '').strip()
    if not text:
        flash('Введите текст жалобы.')
        return redirect(url_for('product', product_id=product_id))
    complaint = Complaint(
        user_id=current_user.id,
        product_id=product_id,
        product_name=product.name,
        text=text,
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(complaint)
    db.session.commit()
    flash('Жалоба отправлена.')
    return redirect(url_for('product', product_id=product_id))

# --- Админ-панель ---
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    return render_template('admin/index.html')

# --- Пользователи ---
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Только главный администратор может управлять пользователями.')
        return redirect(url_for('admin_panel'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        flash('Недостаточно прав.')
        return redirect(url_for('admin_users'))
    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.')
        return redirect(url_for('admin_users'))
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_role = request.form.get('role', 'user')
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                flash('Пользователь с таким логином уже существует.')
                return render_template('admin/edit_user.html', user=user)
            user.username = new_username
        user.role = new_role
        db.session.commit()
        flash('Данные обновлены.')
        return redirect(url_for('admin_users'))
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/<int:user_id>/delete')
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('Недостаточно прав.')
        return redirect(url_for('admin_users'))
    if user_id == current_user.id:
        flash('Нельзя удалить самого себя.')
        return redirect(url_for('admin_users'))
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.username} удалён.')
    return redirect(url_for('admin_users'))

# --- Товары ---
@app.route('/admin/products')
@login_required
def admin_products():
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            category=request.form['category'],
            price=int(request.form['price']),
            desc=request.form['desc'],
            details=request.form['details'],
            image=request.form['image'] or 'https://via.placeholder.com/300x200?text=New'
        )
        original_price = request.form.get('original_price', type=int)
        if original_price:
            product.original_price = original_price
        db.session.add(product)
        db.session.commit()
        flash('Товар добавлен.')
        return redirect(url_for('admin_products'))
    # Исправлено: получаем список строк, а не кортежей
    categories = sorted({p.category for p in Product.query.all()})
    return render_template('admin/add_product.html', categories=categories)

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    product = db.session.get(Product, product_id)
    if not product:
        flash('Товар не найден.')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        product.name = request.form['name']
        product.category = request.form['category']
        product.price = int(request.form['price'])
        product.desc = request.form['desc']
        product.details = request.form['details']
        product.image = request.form['image'] or product.image
        orig_price = request.form.get('original_price', type=int)
        if orig_price:
            product.original_price = orig_price
        else:
            product.original_price = None
        db.session.commit()
        flash('Товар обновлён.')
        return redirect(url_for('admin_products'))
    # Исправлено: получаем список строк
    categories = sorted({p.category for p in Product.query.all()})
    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/<int:product_id>/delete')
@login_required
def admin_delete_product(product_id):
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    product = db.session.get(Product, product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Товар удалён.')
    return redirect(url_for('admin_products'))

# --- Жалобы ---
@app.route('/admin/complaints')
@login_required
def admin_complaints():
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    complaints = Complaint.query.order_by(Complaint.id.desc()).all()
    return render_template('admin/complaints.html', complaints=complaints)

@app.route('/admin/complaints/<int:complaint_id>/reply', methods=['POST'])
@login_required
def admin_reply_complaint(complaint_id):
    if current_user.role not in ('admin', 'subadmin'):
        flash('Доступ запрещён.')
        return redirect(url_for('index'))
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        flash('Жалоба не найдена.')
        return redirect(url_for('admin_complaints'))
    reply_text = request.form.get('reply', '').strip()
    if not reply_text:
        flash('Введите текст ответа.')
        return redirect(url_for('admin_complaints'))
    complaint.reply = reply_text
    complaint.replied_by = current_user.username
    db.session.commit()
    flash('Ответ отправлен.')
    return redirect(url_for('admin_complaints'))

if __name__ == '__main__':
    app.run(debug=True)