from flask import Flask, render_template, request, g, abort
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.root_path, 'pizza.db')

def get_db():
    # Use Flask's application context to store the database connection
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('pizza.db')
        db.row_factory = sqlite3.Row  # Enable dictionary-like access to rows
        # Create tables if they don't exist
        c = db.cursor()
        # Pizza table for storing pizza details
        c.execute('''CREATE TABLE IF NOT EXISTS Pizza (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT
                    )''')
        # Topping table for storing topping details
        c.execute('''CREATE TABLE IF NOT EXISTS Topping (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT
                    )''')
        # PizzaTopping table for linking pizzas with toppings
        c.execute('''CREATE TABLE IF NOT EXISTS PizzaTopping (
                        pizza_id INTEGER,
                        topping_id INTEGER,
                        FOREIGN KEY(pizza_id) REFERENCES Pizza(id),
                        FOREIGN KEY(topping_id) REFERENCES Topping(id),
                        PRIMARY KEY (pizza_id, topping_id)
                    )''')
        # Orders table for storing pizza orders
        c.execute('''CREATE TABLE IF NOT EXISTS Orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        topping TEXT,
                        sauce TEXT,
                        extras TEXT,
                        instructions TEXT,
                        update_time TEXT
                    )''')
        db.commit()
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        name = request.form['name'].strip()
        topping = request.form['topping']
        sauce = request.form['sauce']
        extras = ", ".join(request.form.getlist('extras'))
        instructions = request.form['instructions'].strip()

        # Validate name length (must be between 3 and 20 characters)
        if len(name) < 3 or len(name) > 20:
            print("Name length is invalid") 
            abort(404)

        db = get_db()
        try:
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute("""
                INSERT INTO Orders (name, topping, sauce, extras, instructions,update_time)
                VALUES (?, ?, ?, ?, ?,?)
            """, (name, topping, sauce, extras, instructions,update_time))
            db.commit()
        except sqlite3.IntegrityError:
            db.execute("""
                UPDATE Orders
                SET topping=?, sauce=?, extras=?, instructions=?,update_time=?
                WHERE name=?
            """, (topping, sauce, extras, instructions,update_time, name))
            db.commit()

        return render_template('confirmation.html', name=name)
    return render_template('order_form.html')

# @app.route('/orderlist')
# def orderlist():
#     db = get_db()
#     cursor = db.execute('SELECT * FROM Orders ORDER BY id ASC;')
#     orderlist = cursor.fetchall()
#     print(orderlist)
#     return render_template('test_list.html', orders=orderlist)

@app.route('/orderlist')
def orderList():
    search_query = request.args.get('search', '')
    db = get_db()
    if search_query:
        cursor = db.execute("SELECT * FROM Orders WHERE name LIKE ? ORDER BY id ASC", ('%' + search_query + '%',))
    else:
        cursor = db.execute("SELECT * FROM Orders ORDER BY id ASC")
    orders = cursor.fetchall()
    db.close()
    return render_template('orders_list.html', orders=orders, search_query=search_query)


@app.errorhandler(404)
def not_found(e):
    print(e)
    return render_template("404.html")


if __name__ == '__main__':
    app.run(debug=True)
