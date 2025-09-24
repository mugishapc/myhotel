from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db, get_db_connection
from datetime import datetime, date, timedelta
import functools
import sqlite3

app = Flask(__name__)
app.secret_key = 'd29c234ca310aa6990092d4b6cd4c4854585c51e1f73bf4de510adca03f5bc4e'

# Initialize database
init_db()

def login_required(role=None):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE name = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['name']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required()
def dashboard():
    conn = get_db_connection()
    
    # Get today's date
    today = date.today().isoformat()
    
    # Get total rooms
    total_rooms = conn.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]
    
    # Get available rooms
    available_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'available'"
    ).fetchone()[0]
    
    # Get sold rooms
    sold_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'sold'"
    ).fetchone()[0]
    
    # Get today's income
    today_income = conn.execute(
        'SELECT SUM(price) FROM sales WHERE date = ?',
        (today,)
    ).fetchone()[0] or 0
    
    # Get today's expenses
    today_expenses = conn.execute(
        'SELECT SUM(amount) FROM expenses WHERE date = ?',
        (today,)
    ).fetchone()[0] or 0
    
    # Calculate profit
    profit = today_income - today_expenses
    
    conn.close()
    
    stats = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'sold_rooms': sold_rooms,
        'today_income': today_income,
        'today_expenses': today_expenses,
        'profit': profit
    }
    
    if session['role'] == 'admin':
        return render_template('admin_dashboard.html', stats=stats)
    else:
        return render_template('gestionnaire_dashboard.html', stats=stats)

@app.route('/sell_room', methods=['POST'])
@login_required(role='gestionnaire')
def sell_room():
    room_number = request.form['room_number']
    
    conn = get_db_connection()
    
    # Check if room exists and is available
    room = conn.execute(
        'SELECT * FROM rooms WHERE room_number = ? AND status = "available"',
        (room_number,)
    ).fetchone()
    
    if room:
        # Mark room as sold
        conn.execute(
            'UPDATE rooms SET status = "sold" WHERE room_number = ?',
            (room_number,)
        )
        
        # Record the sale
        today = date.today().isoformat()
        conn.execute(
            'INSERT INTO sales (room_id, gestionnaire_id, date, price) VALUES (?, ?, ?, ?)',
            (room['room_id'], session['user_id'], today, room['price'])
        )
        
        conn.commit()
        conn.close()
        flash(f'Room {room_number} sold successfully!', 'success')
    else:
        conn.close()
        flash(f'Room {room_number} not available or does not exist.', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/add_expense', methods=['POST'])
@login_required(role='gestionnaire')
def add_expense():
    reason = request.form['reason']
    amount = float(request.form['amount'])
    
    conn = get_db_connection()
    today = date.today().isoformat()
    
    conn.execute(
        'INSERT INTO expenses (gestionnaire_id, reason, amount, date) VALUES (?, ?, ?, ?)',
        (session['user_id'], reason, amount, today)
    )
    
    conn.commit()
    conn.close()
    
    flash('Expense recorded successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/rooms')
@login_required()
def rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms ORDER BY room_number').fetchall()
    conn.close()
    
    return render_template('rooms.html', rooms=rooms)

@app.route('/add_room', methods=['POST'])
@login_required(role='admin')
def add_room():
    room_number = request.form['room_number']
    price = float(request.form['price'])
    
    conn = get_db_connection()
    
    try:
        conn.execute(
            'INSERT INTO rooms (room_number, price) VALUES (?, ?)',
            (room_number, price)
        )
        conn.commit()
        flash(f'Room {room_number} added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Room {room_number} already exists.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('rooms'))

@app.route('/delete_room/<int:room_id>')
@login_required(role='admin')
def delete_room(room_id):
    conn = get_db_connection()
    
    # Check if room is sold
    room = conn.execute('SELECT * FROM rooms WHERE room_id = ?', (room_id,)).fetchone()
    
    if room and room['status'] == 'sold':
        flash('Cannot delete a sold room.', 'danger')
    else:
        conn.execute('DELETE FROM rooms WHERE room_id = ?', (room_id,))
        conn.commit()
        flash('Room deleted successfully!', 'success')
    
    conn.close()
    return redirect(url_for('rooms'))

@app.route('/expenses')
@login_required()
def expenses():
    conn = get_db_connection()
    
    if session['role'] == 'admin':
        expenses_list = conn.execute('''
            SELECT e.*, u.name as gestionnaire_name 
            FROM expenses e 
            JOIN users u ON e.gestionnaire_id = u.id 
            ORDER BY e.date DESC
        ''').fetchall()
    else:
        expenses_list = conn.execute('''
            SELECT e.*, u.name as gestionnaire_name 
            FROM expenses e 
            JOIN users u ON e.gestionnaire_id = u.id 
            WHERE e.gestionnaire_id = ?
            ORDER BY e.date DESC
        ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('expenses.html', expenses=expenses_list)

@app.route('/reports')
@login_required()
def reports():
    period = request.args.get('period', 'today')
    
    # Calculate date range based on period
    if period == 'today':
        start_date = end_date = date.today().isoformat()
    elif period == 'week':
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=7)).isoformat()
    elif period == 'month':
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()
    else:
        # Custom date range
        start_date = request.args.get('start_date', date.today().isoformat())
        end_date = request.args.get('end_date', date.today().isoformat())
    
    conn = get_db_connection()
    
    # Get sales data
    sales = conn.execute('''
        SELECT s.*, r.room_number, u.name as gestionnaire_name 
        FROM sales s 
        JOIN rooms r ON s.room_id = r.room_id 
        JOIN users u ON s.gestionnaire_id = u.id 
        WHERE s.date BETWEEN ? AND ?
        ORDER BY s.date DESC
    ''', (start_date, end_date)).fetchall()
    
    # Get expenses data
    expenses = conn.execute('''
        SELECT e.*, u.name as gestionnaire_name 
        FROM expenses e 
        JOIN users u ON e.gestionnaire_id = u.id 
        WHERE e.date BETWEEN ? AND ?
        ORDER BY e.date DESC
    ''', (start_date, end_date)).fetchall()
    
    # Calculate totals
    total_income = conn.execute(
        'SELECT SUM(price) FROM sales WHERE date BETWEEN ? AND ?',
        (start_date, end_date)
    ).fetchone()[0] or 0
    
    total_expenses = conn.execute(
        'SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?',
        (start_date, end_date)
    ).fetchone()[0] or 0
    
    net_profit = total_income - total_expenses
    
    conn.close()
    
    return render_template('reports.html', 
                         sales=sales, 
                         expenses=expenses,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         net_profit=net_profit,
                         period=period,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/delete_report/<string:report_type>/<int:report_id>')
@login_required(role='admin')
def delete_report(report_type, report_id):
    conn = get_db_connection()
    
    if report_type == 'sale':
        # Get the sale record to find the room_id
        sale = conn.execute('SELECT * FROM sales WHERE id = ?', (report_id,)).fetchone()
        if sale:
            # Update room status back to available
            conn.execute('UPDATE rooms SET status = "available" WHERE room_id = ?', (sale['room_id'],))
            # Delete the sale record
            conn.execute('DELETE FROM sales WHERE id = ?', (report_id,))
            flash('Sale report deleted successfully! Room status updated to available.', 'success')
        else:
            flash('Sale report not found!', 'danger')
    elif report_type == 'expense':
        conn.execute('DELETE FROM expenses WHERE id = ?', (report_id,))
        flash('Expense report deleted successfully!', 'success')
    else:
        flash('Invalid report type!', 'danger')
        conn.close()
        return redirect(url_for('reports'))
    
    conn.commit()
    conn.close()
    return redirect(url_for('reports'))

@app.route('/users')
@login_required(role='admin')
def users():
    conn = get_db_connection()
    users_list = conn.execute('SELECT * FROM users WHERE id != ? ORDER BY name', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('users.html', users=users_list)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_user(user_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        password = request.form['password']
        
        try:
            if password:
                conn.execute(
                    'UPDATE users SET name = ?, role = ?, password = ? WHERE id = ?',
                    (name, role, password, user_id)
                )
            else:
                conn.execute(
                    'UPDATE users SET name = ?, role = ? WHERE id = ?',
                    (name, role, user_id)
                )
            conn.commit()
            flash('User updated successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('users'))
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('users'))
    
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>')
@login_required(role='admin')
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('users'))
    
    conn = get_db_connection()
    
    # Check if user has any sales or expenses
    sales_count = conn.execute('SELECT COUNT(*) FROM sales WHERE gestionnaire_id = ?', (user_id,)).fetchone()[0]
    expenses_count = conn.execute('SELECT COUNT(*) FROM expenses WHERE gestionnaire_id = ?', (user_id,)).fetchone()[0]
    
    if sales_count > 0 or expenses_count > 0:
        flash('Cannot delete user with existing sales or expenses records!', 'danger')
    else:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    
    conn.close()
    return redirect(url_for('users'))

@app.route('/add_user', methods=['GET', 'POST'])
@login_required(role='admin')
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        password = request.form['password']
        
        conn = get_db_connection()
        
        try:
            conn.execute(
                'INSERT INTO users (name, role, password) VALUES (?, ?, ?)',
                (name, role, password)
            )
            conn.commit()
            flash(f'User {name} added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash(f'User {name} already exists.', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('add_user'))
    
    return render_template('add_user.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)