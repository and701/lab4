from flask import Flask, render_template, request, redirect, url_for
from models import get_db, close_db, init_db

app = Flask(__name__)
app.config['DATABASE'] = 'db.sqlite'

# Реєструємо функцію закриття з'єднання з БД після кожного запиту
app.teardown_appcontext(close_db)

# Автоматичне створення таблиць при першому запуску
with app.app_context():
    init_db()

# --- СТАРІ МАРШРУТИ З МЕНЮ ---
@app.route('/', endpoint='home')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/tournaments')
def tournaments():
    return render_template('tournaments.html')

# --- 1. ВІДГУКИ ТА АДМІН-ПАНЕЛЬ ДЛЯ НИХ ---
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message']
        db.execute('INSERT INTO feedback (name, message) VALUES (?, ?)', (name, message))
        db.commit()
        return redirect(url_for('feedback'))
    
    feedbacks = db.execute('SELECT * FROM feedback ORDER BY id DESC').fetchall()
    return render_template('feedback.html', feedbacks=feedbacks)

@app.route('/admin/feedback/delete/<int:id>', methods=['POST'])
def delete_feedback(id):
    db = get_db()
    db.execute('DELETE FROM feedback WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('admin_panel'))

# --- 2. МАГАЗИН ТА ЗАМОВЛЕННЯ ---
@app.route('/shop')
def shop():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('shop.html', products=products)

@app.route('/shop/add_product', methods=['POST'])
def add_product():
    title = request.form['title']
    price = request.form['price']
    description = request.form['description']
    
    db = get_db()
    db.execute('INSERT INTO products (title, price, description) VALUES (?, ?, ?)', (title, price, description))
    db.commit()
    return redirect(url_for('shop'))

@app.route('/shop/order/<int:product_id>', methods=['POST'])
def create_order(product_id):
    customer_name = request.form['customer_name']
    db = get_db()
    
    cursor = db.execute('INSERT INTO orders (customer_name, status) VALUES (?, ?)', (customer_name, 'Нове'))
    order_id = cursor.lastrowid
    
    db.execute('INSERT INTO order_items (order_id, product_id) VALUES (?, ?)', (order_id, product_id))
    db.commit()
    return redirect(url_for('shop'))

@app.route('/admin/order/status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    new_status = request.form['status']
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    db.commit()
    return redirect(url_for('admin_panel'))

# --- 3. ГОЛОВНА АДМІН-ПАНЕЛЬ ---
@app.route('/admin')
def admin_panel():
    db = get_db()
    feedbacks = db.execute('SELECT * FROM feedback ORDER BY id DESC').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    
    orders = db.execute('''
        SELECT orders.id, orders.customer_name, orders.status, products.title, products.price 
        FROM orders 
        JOIN order_items ON orders.id = order_items.order_id 
        JOIN products ON order_items.product_id = products.id
    ''').fetchall()
    
    return render_template('admin.html', feedbacks=feedbacks, products=products, orders=orders)

if __name__ == '__main__':
    app.run(debug=True)