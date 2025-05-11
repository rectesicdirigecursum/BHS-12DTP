from flask import Flask, render_template, request, abort, g
from datetime import datetime
import sqlite3

# Create Flask application
app = Flask(__name__)

# Function to get the database connection
# Creates the database and tables if they don't exist
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

# Close the database connection after each request
@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Home page route
@app.route('/')
def home():
    return render_template('home.html', title='HOME')

# About page route
@app.route('/about')
def about():
    return render_template('about.html', title='ABOUT')

# Test page route
@app.route('/test')
def test():
    return render_template('test.html', title='TEST')

# Route to list all pizzas
@app.route('/all_pizzas')
def all_pizzas():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id,name FROM Pizza ORDER BY name ASC')
    pizzas = c.fetchall()
    return render_template('all_pizzas.html', title='ALL PIZZAS', pizzas=pizzas)

# Route to show details of a specific pizza
@app.route('/pizza/<int:id>')
def pizza(id):
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM Pizza WHERE id = ?', (id,))
    pizza = c.fetchone()
    if pizza is None:
        abort(404)
    c.execute('SELECT t.name FROM Topping t JOIN PizzaTopping pt ON t.id = pt.topping_id WHERE pt.pizza_id = ?', (id,))
    toppings = [row['name'] for row in c.fetchall()]
    return render_template('pizza.html', title=pizza['name'].upper() + ' PIZZA', pizza=pizza, toppings=toppings)

# Route for pizza order form and submission
@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        # Get form data
        name = request.form['name'].strip()
        # Validate name length (must be between 3 and 20 characters)
        if len(name) < 3 or len(name) > 20:
            abort(404)
        topping = request.form['topping']
        sauce = request.form['sauce']
        extras = ", ".join(request.form.getlist('extras'))
        instructions = request.form['instructions'].strip()
        # Get current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db = get_db()
        c = db.cursor()
        try:
            # Insert new order into the database
            c.execute('INSERT INTO Orders (name, topping, sauce, extras, instructions, update_time) VALUES (?, ?, ?, ?, ?, ?)',
                      (name, topping, sauce, extras, instructions, now))
            db.commit()
        except sqlite3.IntegrityError:
            # If an order with the same name exists, update it instead
            c.execute('UPDATE Orders SET topping = ?, sauce = ?, extras = ?, instructions = ?, update_time = ? WHERE name = ?',
                      (topping, sauce, extras, instructions, now, name))
            db.commit()
        # Render confirmation page with order details
        return render_template('confirmation.html', name=name, topping=topping, sauce=sauce, extras=extras, instructions=instructions)
    # For GET request, render the order form
    return render_template('order_form.html')

# Route to list all orders
@app.route('/orderList')
def orderList():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id,name,topping,sauce,extras,instructions,update_time FROM Orders ORDER BY id ASC')
    orders = c.fetchall()
    return render_template('orders_list.html', orders=orders)

# Custom 404 error handler
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)