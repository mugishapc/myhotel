from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from database import init_db, get_db_connection
from datetime import datetime, date, timedelta
import functools
import sqlite3
import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

app = Flask(__name__)
app.secret_key = 'd29c234ca310aa6990092d4b6cd4c4854585c51e1f73bf4de510adca03f5bc4e'

# Initialize database
init_db()

# Register fonts (optional - for better formatting)
try:
    pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica.ttf'))
except:
    pass  # Use default font if Helvetica not available

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

# PWA Manifest and Service Worker Routes
@app.route('/manifest.json')
def manifest():
    return send_file('manifest.json', mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return send_file('sw.js', mimetype='application/javascript')

@app.route('/offline')
def offline():
    return render_template('offline.html')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE name=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
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
    cursor = conn.cursor()
    
    # Get today's date
    today = date.today().isoformat()
    
    try:
        # Get total rooms
        cursor.execute('SELECT COUNT(*) as count FROM rooms')
        total_rooms = cursor.fetchone()['count']
        
        # Get available rooms
        cursor.execute("SELECT COUNT(*) as count FROM rooms WHERE status = 'available'")
        available_rooms = cursor.fetchone()['count']
        
        # Get sold rooms
        cursor.execute("SELECT COUNT(*) as count FROM rooms WHERE status = 'sold'")
        sold_rooms = cursor.fetchone()['count']
        
        # Get today's income
        cursor.execute('SELECT SUM(price) as sum FROM sales WHERE date = ?', (today,))
        today_income_result = cursor.fetchone()['sum']
        today_income = today_income_result if today_income_result else 0
        
        # Get today's expenses
        cursor.execute('SELECT SUM(amount) as sum FROM expenses WHERE date = ?', (today,))
        today_expenses_result = cursor.fetchone()['sum']
        today_expenses = today_expenses_result if today_expenses_result else 0
        
        # Calculate profit
        profit = today_income - today_expenses
        
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
            
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('login'))
    finally:
        cursor.close()
        conn.close()

@app.route('/sell_room', methods=['POST'])
@login_required(role='gestionnaire')
def sell_room():
    room_number = request.form['room_number']
    sale_type = request.form['sale_type']  # 'full' or 'passage'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if room exists and is available
        cursor.execute(
            'SELECT * FROM rooms WHERE room_number = ? AND status = ?',
            (room_number, 'available')
        )
        room = cursor.fetchone()
        
        if room:
            # Determine price based on sale type
            if sale_type == 'full':
                price = room['price_full']
            else:  # passage
                price = room['price_passage']
            
            # Mark room as sold
            cursor.execute(
                'UPDATE rooms SET status = ? WHERE room_number = ?',
                ('sold', room_number)
            )
            
            # Record the sale with type information
            today = date.today().isoformat()
            cursor.execute(
                'INSERT INTO sales (room_id, gestionnaire_id, date, price, status, sale_type) VALUES (?, ?, ?, ?, ?, ?)',
                (room['room_id'], session['user_id'], today, price, 'active', sale_type)
            )
            
            conn.commit()
            
            # Convert price to BIF for display
            price_bif = f"{price:,.0f} BIF"
            flash(f'Room {room_number} sold successfully as {sale_type.upper()} for {price_bif}!', 'success')
        else:
            flash(f'Room {room_number} not available or does not exist.', 'danger')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error selling room: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/restore_room', methods=['POST'])
@login_required(role='gestionnaire')
def restore_room():
    room_number = request.form['room_number']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if room exists and is sold
        cursor.execute(
            'SELECT * FROM rooms WHERE room_number = ? AND status = ?',
            (room_number, 'sold')
        )
        room = cursor.fetchone()
        
        if room:
            # Check if there's an active sale for this room by the current gestionnaire
            cursor.execute(
                'SELECT * FROM sales WHERE room_id = ? AND gestionnaire_id = ? AND status = ?',
                (room['room_id'], session['user_id'], 'active')
            )
            active_sale = cursor.fetchone()
            
            if active_sale:
                # Mark room as available
                cursor.execute(
                    'UPDATE rooms SET status = ? WHERE room_number = ?',
                    ('available', room_number)
                )
                
                # Update the sale status to 'restored'
                cursor.execute(
                    'UPDATE sales SET status = ?, restore_date = ? WHERE id = ?',
                    ('restored', date.today().isoformat(), active_sale['id'])
                )
                
                conn.commit()
                flash(f'Room {room_number} restored successfully! Clients have left the room.', 'success')
            else:
                flash(f'No active sale found for room {room_number} under your account.', 'danger')
        else:
            flash(f'Room {room_number} is not sold or does not exist.', 'danger')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error restoring room: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/add_expense', methods=['POST'])
@login_required(role='gestionnaire')
def add_expense():
    reason = request.form['reason']
    amount = float(request.form['amount'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        today = date.today().isoformat()
        
        cursor.execute(
            'INSERT INTO expenses (gestionnaire_id, reason, amount, date) VALUES (?, ?, ?, ?)',
            (session['user_id'], reason, amount, today)
        )
        
        conn.commit()
        flash('Expense recorded successfully!', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error recording expense: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/rooms')
@login_required()
def rooms():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM rooms ORDER BY room_number')
        rooms = cursor.fetchall()
        return render_template('rooms.html', rooms=rooms)
    except Exception as e:
        flash(f'Error loading rooms: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/add_room', methods=['POST'])
@login_required(role='admin')
def add_room():
    room_number = request.form['room_number']
    price_full = float(request.form['price_full'])
    price_passage = float(request.form['price_passage'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO rooms (room_number, price_full, price_passage) VALUES (?, ?, ?)',
            (room_number, price_full, price_passage)
        )
        conn.commit()
        
        # Convert prices to BIF for display message
        price_full_bif = f"{price_full:,.0f} BIF"
        price_passage_bif = f"{price_passage:,.0f} BIF"
        
        flash(f'Room {room_number} added successfully! This room costs {price_full_bif} for FULL and {price_passage_bif} for PASSAGE.', 'success')
    
    except Exception as e:
        conn.rollback()
        if 'unique constraint' in str(e).lower():
            flash(f'Room {room_number} already exists.', 'danger')
        else:
            flash(f'Error adding room: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('rooms'))

@app.route('/delete_room/<int:room_id>')
@login_required(role='admin')
def delete_room(room_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if room is sold
        cursor.execute('SELECT * FROM rooms WHERE room_id = ?', (room_id,))
        room = cursor.fetchone()
        
        if room and room['status'] == 'sold':
            flash('Cannot delete a sold room.', 'danger')
        else:
            cursor.execute('DELETE FROM rooms WHERE room_id = ?', (room_id,))
            conn.commit()
            flash('Room deleted successfully!', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting room: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('rooms'))

@app.route('/expenses')
@login_required()
def expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if session['role'] == 'admin':
            cursor.execute('''
                SELECT e.*, u.name as gestionnaire_name 
                FROM expenses e 
                JOIN users u ON e.gestionnaire_id = u.id 
                ORDER BY e.date DESC
            ''')
        else:
            cursor.execute('''
                SELECT e.*, u.name as gestionnaire_name 
                FROM expenses e 
                JOIN users u ON e.gestionnaire_id = u.id 
                WHERE e.gestionnaire_id = ?
                ORDER BY e.date DESC
            ''', (session['user_id'],))
        
        expenses_list = cursor.fetchall()
        return render_template('expenses.html', expenses=expenses_list)
    
    except Exception as e:
        flash(f'Error loading expenses: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

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
    cursor = conn.cursor()
    
    try:
        # Get sales data
        if session['role'] == 'admin':
            cursor.execute('''
                SELECT s.*, r.room_number, u.name as gestionnaire_name 
                FROM sales s 
                JOIN rooms r ON s.room_id = r.room_id 
                JOIN users u ON s.gestionnaire_id = u.id 
                WHERE s.date BETWEEN ? AND ?
                ORDER BY s.date DESC
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT s.*, r.room_number, u.name as gestionnaire_name 
                FROM sales s 
                JOIN rooms r ON s.room_id = r.room_id 
                JOIN users u ON s.gestionnaire_id = u.id 
                WHERE s.gestionnaire_id = ? AND s.date BETWEEN ? AND ?
                ORDER BY s.date DESC
            ''', (session['user_id'], start_date, end_date))
        
        sales = cursor.fetchall()
        
        # Get expenses data
        if session['role'] == 'admin':
            cursor.execute('''
                SELECT e.*, u.name as gestionnaire_name 
                FROM expenses e 
                JOIN users u ON e.gestionnaire_id = u.id 
                WHERE e.date BETWEEN ? AND ?
                ORDER BY e.date DESC
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT e.*, u.name as gestionnaire_name 
                FROM expenses e 
                JOIN users u ON e.gestionnaire_id = u.id 
                WHERE e.gestionnaire_id = ? AND e.date BETWEEN ? AND ?
                ORDER BY e.date DESC
            ''', (session['user_id'], start_date, end_date))
        
        expenses = cursor.fetchall()
        
        # Calculate totals
        if session['role'] == 'admin':
            cursor.execute(
                'SELECT SUM(price) as sum FROM sales WHERE date BETWEEN ? AND ?',
                (start_date, end_date)
            )
            total_income_result = cursor.fetchone()['sum']
            total_income = total_income_result if total_income_result else 0
            
            cursor.execute(
                'SELECT SUM(amount) as sum FROM expenses WHERE date BETWEEN ? AND ?',
                (start_date, end_date)
            )
            total_expenses_result = cursor.fetchone()['sum']
            total_expenses = total_expenses_result if total_expenses_result else 0
        else:
            cursor.execute(
                'SELECT SUM(price) as sum FROM sales WHERE gestionnaire_id = ? AND date BETWEEN ? AND ?',
                (session['user_id'], start_date, end_date)
            )
            total_income_result = cursor.fetchone()['sum']
            total_income = total_income_result if total_income_result else 0
            
            cursor.execute(
                'SELECT SUM(amount) as sum FROM expenses WHERE gestionnaire_id = ? AND date BETWEEN ? AND ?',
                (session['user_id'], start_date, end_date)
            )
            total_expenses_result = cursor.fetchone()['sum']
            total_expenses = total_expenses_result if total_expenses_result else 0
        
        net_profit = total_income - total_expenses
        
        return render_template('reports.html', 
                             sales=sales, 
                             expenses=expenses,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             net_profit=net_profit,
                             period=period,
                             start_date=start_date,
                             end_date=end_date)
    
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

def create_pdf_report(start_date, end_date, sales, expenses, total_income, total_expenses, net_profit):
    """Create a PDF report with proper formatting"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center aligned
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Build story (content)
    story = []
    
    # Title
    story.append(Paragraph("CRESCENT HOTEL - RAPPORT HEBDOMADAIRE", title_style))
    story.append(Paragraph(f"Période: {start_date} à {end_date}", normal_style))
    story.append(Spacer(1, 20))
    
    # Summary Section
    story.append(Paragraph("RÉSUMÉ", heading_style))
    
    summary_data = [
        ['Revenu Total:', f"{total_income:,.0f} BIF"],
        ['Dépenses Total:', f"{total_expenses:,.0f} BIF"],
        ['Profit Net:', f"{net_profit:,.0f} BIF"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Sales Section
    story.append(Paragraph("VENTES", heading_style))
    
    if sales:
        sales_data = [['Date', 'Chambre', 'Gestionnaire', 'Type', 'Prix (BIF)', 'Statut']]
        
        for sale in sales:
            sales_data.append([
                sale['date'],
                sale['room_number'],
                sale['gestionnaire_name'],
                sale['sale_type'].upper(),
                f"{sale['price']:,.0f}",
                sale['status']
            ])
        
        sales_table = Table(sales_data, repeatRows=1)
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(sales_table)
    else:
        story.append(Paragraph("Aucune vente trouvée pour cette période.", normal_style))
    
    story.append(Spacer(1, 30))
    
    # Expenses Section
    story.append(Paragraph("DÉPENSES", heading_style))
    
    if expenses:
        expenses_data = [['Date', 'Gestionnaire', 'Raison', 'Montant (BIF)']]
        
        for expense in expenses:
            expenses_data.append([
                expense['date'],
                expense['gestionnaire_name'],
                expense['reason'],
                f"{expense['amount']:,.0f}"
            ])
        
        expenses_table = Table(expenses_data, repeatRows=1)
        expenses_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(expenses_table)
    else:
        story.append(Paragraph("Aucune dépense trouvée pour cette période.", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/download_pdf_report')
@login_required(role='admin')
def download_pdf_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        flash('Please select both start and end dates.', 'danger')
        return redirect(url_for('reports'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get sales data for the selected period
        cursor.execute('''
            SELECT s.*, r.room_number, u.name as gestionnaire_name 
            FROM sales s 
            JOIN rooms r ON s.room_id = r.room_id 
            JOIN users u ON s.gestionnaire_id = u.id 
            WHERE s.date BETWEEN ? AND ?
            ORDER BY s.date DESC
        ''', (start_date, end_date))
        sales = cursor.fetchall()
        
        # Get expenses data for the selected period
        cursor.execute('''
            SELECT e.*, u.name as gestionnaire_name 
            FROM expenses e 
            JOIN users u ON e.gestionnaire_id = u.id 
            WHERE e.date BETWEEN ? AND ?
            ORDER BY e.date DESC
        ''', (start_date, end_date))
        expenses = cursor.fetchall()
        
        # Calculate totals
        cursor.execute(
            'SELECT SUM(price) as sum FROM sales WHERE date BETWEEN ? AND ?',
            (start_date, end_date)
        )
        total_income_result = cursor.fetchone()['sum']
        total_income = total_income_result if total_income_result else 0
        
        cursor.execute(
            'SELECT SUM(amount) as sum FROM expenses WHERE date BETWEEN ? AND ?',
            (start_date, end_date)
        )
        total_expenses_result = cursor.fetchone()['sum']
        total_expenses = total_expenses_result if total_expenses_result else 0
        
        net_profit = total_income - total_expenses
        
        # Create PDF
        pdf_buffer = create_pdf_report(start_date, end_date, sales, expenses, total_income, total_expenses, net_profit)
        
        filename = f"rapport_hebdomadaire_{start_date}_a_{end_date}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        flash(f'Error generating PDF report: {str(e)}', 'danger')
        return redirect(url_for('reports'))
    finally:
        cursor.close()
        conn.close()

@app.route('/download_weekly_report')
@login_required(role='admin')
def download_weekly_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        flash('Please select both start and end dates.', 'danger')
        return redirect(url_for('reports'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get sales data for the selected period
        cursor.execute('''
            SELECT s.*, r.room_number, u.name as gestionnaire_name 
            FROM sales s 
            JOIN rooms r ON s.room_id = r.room_id 
            JOIN users u ON s.gestionnaire_id = u.id 
            WHERE s.date BETWEEN ? AND ?
            ORDER BY s.date DESC
        ''', (start_date, end_date))
        sales = cursor.fetchall()
        
        # Get expenses data for the selected period
        cursor.execute('''
            SELECT e.*, u.name as gestionnaire_name 
            FROM expenses e 
            JOIN users u ON e.gestionnaire_id = u.id 
            WHERE e.date BETWEEN ? AND ?
            ORDER BY e.date DESC
        ''', (start_date, end_date))
        expenses = cursor.fetchall()
        
        # Calculate totals
        cursor.execute(
            'SELECT SUM(price) as sum FROM sales WHERE date BETWEEN ? AND ?',
            (start_date, end_date)
        )
        total_income_result = cursor.fetchone()['sum']
        total_income = total_income_result if total_income_result else 0
        
        cursor.execute(
            'SELECT SUM(amount) as sum FROM expenses WHERE date BETWEEN ? AND ?',
            (start_date, end_date)
        )
        total_expenses_result = cursor.fetchone()['sum']
        total_expenses = total_expenses_result if total_expenses_result else 0
        
        net_profit = total_income - total_expenses
        
        # Create CSV file in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Rapport Hebdomadaire - Crescent Hotel'])
        writer.writerow([f'Période: {start_date} à {end_date}'])
        writer.writerow([])
        
        # Write sales section
        writer.writerow(['VENTES'])
        writer.writerow(['Date', 'Chambre', 'Gestionnaire', 'Type', 'Prix (BIF)', 'Statut'])
        
        for sale in sales:
            writer.writerow([
                sale['date'],
                sale['room_number'],
                sale['gestionnaire_name'],
                sale['sale_type'].upper(),
                f"{sale['price']:,.0f}",
                sale['status']
            ])
        
        writer.writerow([])
        
        # Write expenses section
        writer.writerow(['DÉPENSES'])
        writer.writerow(['Date', 'Gestionnaire', 'Raison', 'Montant (BIF)'])
        
        for expense in expenses:
            writer.writerow([
                expense['date'],
                expense['gestionnaire_name'],
                expense['reason'],
                f"{expense['amount']:,.0f}"
            ])
        
        writer.writerow([])
        
        # Write summary
        writer.writerow(['RÉSUMÉ'])
        writer.writerow(['Revenu Total:', f"{total_income:,.0f} BIF"])
        writer.writerow(['Dépenses Total:', f"{total_expenses:,.0f} BIF"])
        writer.writerow(['Profit Net:', f"{net_profit:,.0f} BIF"])
        writer.writerow([])
        writer.writerow(['Généré le:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        # Prepare file for download
        output.seek(0)
        
        filename = f"rapport_hebdomadaire_{start_date}_a_{end_date}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        flash(f'Error generating CSV report: {str(e)}', 'danger')
        return redirect(url_for('reports'))
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_report/<string:report_type>/<int:report_id>')
@login_required(role='admin')
def delete_report(report_type, report_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if report_type == 'sale':
            # Get the sale record to find the room_id
            cursor.execute('SELECT * FROM sales WHERE id = ?', (report_id,))
            sale = cursor.fetchone()
            if sale:
                # Update room status back to available
                cursor.execute('UPDATE rooms SET status = ? WHERE room_id = ?', ('available', sale['room_id']))
                # Delete the sale record
                cursor.execute('DELETE FROM sales WHERE id = ?', (report_id,))
                conn.commit()
                flash('Sale report deleted successfully! Room status updated to available.', 'success')
            else:
                flash('Sale report not found!', 'danger')
        elif report_type == 'expense':
            cursor.execute('DELETE FROM expenses WHERE id = ?', (report_id,))
            conn.commit()
            flash('Expense report deleted successfully!', 'success')
        else:
            flash('Invalid report type!', 'danger')
            return redirect(url_for('reports'))
    
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting report: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('reports'))

@app.route('/users')
@login_required(role='admin')
def users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY name', (session['user_id'],))
        users_list = cursor.fetchall()
        return render_template('users.html', users=users_list)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        password = request.form['password']
        
        try:
            if password:
                cursor.execute(
                    'UPDATE users SET name = ?, role = ?, password = ? WHERE id = ?',
                    (name, role, password, user_id)
                )
            else:
                cursor.execute(
                    'UPDATE users SET name = ?, role = ? WHERE id = ?',
                    (name, role, user_id)
                )
            conn.commit()
            flash('User updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            if 'unique constraint' in str(e).lower():
                flash('Username already exists!', 'danger')
            else:
                flash(f'Error updating user: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('users'))
    
    try:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('users'))
        
        return render_template('edit_user.html', user=user)
    
    except Exception as e:
        flash(f'Error loading user: {str(e)}', 'danger')
        return redirect(url_for('users'))
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_user/<int:user_id>')
@login_required(role='admin')
def delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('users'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user has any sales or expenses
        cursor.execute('SELECT COUNT(*) as count FROM sales WHERE gestionnaire_id = ?', (user_id,))
        sales_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM expenses WHERE gestionnaire_id = ?', (user_id,))
        expenses_count = cursor.fetchone()['count']
        
        if sales_count > 0 or expenses_count > 0:
            flash('Cannot delete user with existing sales or expenses records!', 'danger')
        else:
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            flash('User deleted successfully!', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    finally:
        cursor.close()
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
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (name, role, password) VALUES (?, ?, ?)',
                (name, role, password)
            )
            conn.commit()
            flash(f'User {name} added successfully!', 'success')
        except Exception as e:
            conn.rollback()
            if 'unique constraint' in str(e).lower():
                flash(f'User {name} already exists.', 'danger')
            else:
                flash(f'Error adding user: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('add_user'))
    
    return render_template('add_user.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT automatically
    app.run(host='0.0.0.0', port=port)