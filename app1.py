from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime, timedelta
import random
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Database Connection Class
class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Milan@721166',
            database='login_system'
        )

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        with self.connection.cursor(buffered=True, dictionary=True) as cursor:
            cursor.execute(query, params or ())
            result = None
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            return result

    def execute_update(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or ())
            self.connection.commit()

    def close(self):
        self.connection.close()

# Decorator to check if admin is logged in
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if faculty is logged in
def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'facility_name' not in session:
            return redirect(url_for('faculty_login'))
        return f(*args, **kwargs)
    return decorated_function

# Generate Routine Function with Advanced Optimization
def generate_routine():
    db = Database()

    # Check if an approved routine already exists
    approved_routine = db.execute_query("SELECT * FROM routine WHERE status = 'approved'", fetch_one=True)

    if approved_routine:
        db.close()
        return {"success": False, "message": "An approved routine already exists."}

    # Fetch all batches and their subjects
    batches = db.execute_query("""
        SELECT b.id AS batch_id, b.batch_name, GROUP_CONCAT(s.skill_name) AS subjects
        FROM batches b
        LEFT JOIN batch_subjects bs ON b.id = bs.batch_id
        LEFT JOIN skills s ON bs.subject_id = s.id
        GROUP BY b.id
    """, fetch_all=True)

    # Fetch all facilities and their skills
    facilities = db.execute_query("""
        SELECT f.id AS facility_id, f.facility_name, GROUP_CONCAT(s.skill_name) AS skills
        FROM facilities f
        LEFT JOIN facility_skills fs ON f.id = fs.facility_id
        LEFT JOIN skills s ON fs.skill_id = s.id
        GROUP BY f.id
    """, fetch_all=True)

    # Fetch existing routine to check facility and room availability
    existing_routine = db.execute_query("SELECT * FROM routine WHERE status = 'draft'", fetch_all=True)

    # Initialize routine as an empty list
    routine = []

    # Define days of the week (Monday to Friday)
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Define time slots (e.g., 9:00 AM to 5:00 PM, 1-hour slots)
    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("17:00", "%H:%M")
    time_slots = []
    current_time = start_time
    while current_time < end_time:
        # Skip the break time (1:00 PM - 2:00 PM)
        if current_time != datetime.strptime("13:00", "%H:%M"):
            time_slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(hours=1)

    # Generate routine for each batch
    for batch in batches:
        batch_id = batch['batch_id']
        batch_name = batch['batch_name']
        subjects = batch['subjects'].split(',') if batch['subjects'] else []

        # Assign subjects to time slots for each day
        for day in days_of_week:
            for i, subject in enumerate(subjects):
                if i < len(time_slots):
                    time_slot = time_slots[i]

                    # Find all facilities that support this subject
                    eligible_facilities = [
                        facility for facility in facilities
                        if subject in facility['skills'].split(',')
                    ]

                    if eligible_facilities:
                        # Shuffle eligible facilities to randomize selection
                        random.shuffle(eligible_facilities)

                        # Try to assign a facility and room
                        for facility in eligible_facilities:
                            # Check if the facility is already assigned at this time slot on this day
                            facility_assigned = any(
                                entry['facility_id'] == facility['facility_id'] and
                                entry['time_slot'] == time_slot and
                                entry['day'] == day
                                for entry in existing_routine
                            )

                            if facility_assigned:
                                continue

                            # Assign a random room number (1-10)
                            room_number = random.randint(1, 10)

                            # Check if the room is already assigned at this time slot on this day
                            room_assigned = any(
                                entry['room_number'] == room_number and
                                entry['time_slot'] == time_slot and
                                entry['day'] == day
                                for entry in existing_routine
                            )

                            if room_assigned:
                                continue

                            # Assign the facility and room
                            routine.append({
                                "batch_id": batch_id,
                                "batch_name": batch_name,
                                "subject": subject,
                                "facility_id": facility['facility_id'],
                                "facility_name": facility['facility_name'],
                                "room_number": room_number,
                                "time_slot": time_slot,
                                "day": day
                            })
                            break
                    else:
                        # If no facility is available, skip this subject
                        continue

    # Delete existing draft routine
    db.execute_update("DELETE FROM routine WHERE status = 'draft'")

    # Save the generated routine to the database
    for entry in routine:
        db.execute_update("""
            INSERT INTO routine (batch_id, batch_name, subject, facility_id, facility_name, room_number, time_slot, day, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'draft')
        """, (
            entry['batch_id'], entry['batch_name'], entry['subject'],
            entry['facility_id'], entry['facility_name'], entry['room_number'], entry['time_slot'], entry['day']
        ))

    db.close()
    return {"success": True, "routine": routine}

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Admin Login Route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required."})

        db = Database()
        user = db.execute_query("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password), fetch_one=True)
        db.close()

        if user:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({"success": True, "message": "Login successful!"})
        else:
            return jsonify({"success": False, "message": "Invalid username or password."})

    return render_template('admin_login.html')

# Admin Dashboard Route
@app.route('/admin/admin_dashboard')
@admin_required
def admin_dashboard():
    db = Database()
    facilities = db.execute_query("""
        SELECT f.id, f.facility_name, GROUP_CONCAT(s.skill_name) AS skill_names
        FROM facilities f
        LEFT JOIN facility_skills fs ON f.id = fs.facility_id
        LEFT JOIN skills s ON fs.skill_id = s.id
        GROUP BY f.id
    """, fetch_all=True)

    for facility in facilities:
        facility['skills'] = facility['skill_names'].split(',') if facility['skill_names'] else []

    skills = db.execute_query("SELECT * FROM skills", fetch_all=True)

    batches = db.execute_query("""
        SELECT b.id, b.batch_name, GROUP_CONCAT(s.skill_name) AS subject_names
        FROM batches b
        LEFT JOIN batch_subjects bs ON b.id = bs.batch_id
        LEFT JOIN skills s ON bs.subject_id = s.id
        GROUP BY b.id
    """, fetch_all=True)

    for batch in batches:
        batch['subjects'] = batch['subject_names'].split(',') if batch['subject_names'] else []

    routine = generate_routine()
    db.close()

    return render_template('admin_dashboard.html', facilities=facilities, batches=batches, skills=skills, routine=routine)

# Approve Routine Route
@app.route('/admin/approve_routine', methods=['POST'])
@admin_required
def approve_routine():
    db = Database()
    db.execute_update("UPDATE routine SET status = 'approved' WHERE status = 'draft'")
    db.close()
    flash("Routine approved successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# View Routine Route
@app.route('/admin/view_routine')
@admin_required
def view_routine():
    db = Database()
    approved_routine = db.execute_query("SELECT * FROM routine WHERE status = 'approved'", fetch_all=True)
    db.close()
    return render_template('view_routine.html', routine=approved_routine)

# Add Facility Route
@app.route('/add_facility', methods=['POST'])
@admin_required
def add_facility():
    facility_name = request.form['facility_name']
    selected_skills = request.form.getlist('facility_skills')

    db = Database()
    cursor = db.connection.cursor()
    cursor.execute("INSERT INTO facilities (facility_name) VALUES (%s)", (facility_name,))
    facility_id = cursor.lastrowid

    for skill_id in selected_skills:
        cursor.execute("INSERT INTO facility_skills (facility_id, skill_id) VALUES (%s, %s)", (facility_id, skill_id))

    db.connection.commit()
    cursor.close()
    db.close()
    return redirect(url_for('admin_dashboard'))

# Delete Facility Route
@app.route('/delete_facility/<int:facility_id>', methods=['POST'])
@admin_required
def delete_facility(facility_id):
    db = Database()
    cursor = db.connection.cursor()

    try:
        cursor.execute("DELETE FROM facility_skills WHERE facility_id = %s", (facility_id,))
        cursor.execute("DELETE FROM facilities WHERE id = %s", (facility_id,))
        db.connection.commit()
        flash("Facility deleted successfully!", "success")
    except mysql.connector.Error as err:
        db.connection.rollback()
        flash(f"Error deleting facility: {err}", "error")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('admin_dashboard'))

# Add Batch Route
@app.route('/add_batch', methods=['POST'])
@admin_required
def add_batch():
    batch_name = request.form['batch_name']
    selected_subjects = request.form.getlist('batch_subjects')

    db = Database()
    cursor = db.connection.cursor()
    cursor.execute("INSERT INTO batches (batch_name) VALUES (%s)", (batch_name,))
    batch_id = cursor.lastrowid

    for subject_id in selected_subjects:
        cursor.execute("INSERT INTO batch_subjects (batch_id, subject_id) VALUES (%s, %s)", (batch_id, subject_id))

    db.connection.commit()
    cursor.close()
    db.close()
    return redirect(url_for('admin_dashboard'))

# Delete Batch Route
@app.route('/delete_batch/<int:batch_id>', methods=['POST'])
@admin_required
def delete_batch(batch_id):
    db = Database()
    cursor = db.connection.cursor()

    try:
        cursor.execute("DELETE FROM routine WHERE batch_id = %s", (batch_id,))
        cursor.execute("DELETE FROM batch_subjects WHERE batch_id = %s", (batch_id,))
        cursor.execute("DELETE FROM batches WHERE id = %s", (batch_id,))
        db.connection.commit()
        flash("Batch deleted successfully!", "success")
    except mysql.connector.Error as err:
        db.connection.rollback()
        flash(f"Error deleting batch: {err}", "error")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('admin_dashboard'))

# Add Skill Route
@app.route('/add_skill', methods=['POST'])
@admin_required
def add_skill():
    skill_name = request.form['skill_name']

    db = Database()
    cursor = db.connection.cursor()
    cursor.execute("INSERT INTO skills (skill_name) VALUES (%s)", (skill_name,))
    db.connection.commit()
    cursor.close()
    db.close()

    return redirect(url_for('admin_dashboard'))

# Faculty Login Route
@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        facility_id = request.form.get('facility_id')

        if not facility_id:
            return "Facility selection is required.", 400

        db = Database()
        try:
            # Fetch facility details using the selected facility_id
            facility = db.execute_query(
                "SELECT id, facility_name FROM facilities WHERE id = %s",
                (facility_id,),
                fetch_one=True
            )
        except Exception as e:
            return f"An error occurred while fetching facility data: {str(e)}", 500
        finally:
            db.close()

        if facility:
            # Store both facility ID and name in the session
            session['facility_id'] = facility['id']
            session['facility_name'] = facility['facility_name']
            return redirect(url_for('facility_classes'))
        else:
            return "Facility not found.", 404

    # For GET requests, fetch all facilities to populate the dropdown
    db = Database()
    try:
        facilities = db.execute_query("SELECT id, facility_name FROM facilities", fetch_all=True)
    except Exception as e:
        return f"An error occurred while fetching facilities: {str(e)}", 500
    finally:
        db.close()

    return render_template('faculty_login.html', facilities=facilities)

# Faculty Classes Route
@app.route('/facility_classes')
@faculty_required
def facility_classes():
    # Retrieve facility_id and facility_name from the session
    facility_id = session.get('facility_id')
    facility_name = session.get('facility_name')

    if not facility_id:
        return "Facility not logged in.", 401

    db = Database()
    try:
        # Fetch classes for the logged-in facility using facility_id
        classes = db.execute_query(
            """
            SELECT day, batch_name, subject, room_number, time_slot 
            FROM routine 
            WHERE facility_id = %s
            ORDER BY day, time_slot
            """,
            (facility_id,),
            fetch_all=True
        )
    except Exception as e:
        return f"An error occurred while fetching classes: {str(e)}", 500
    finally:
        db.close()

    # Render the template with the fetched classes and facility name
    return render_template('facility_classes.html', classes=classes, facility_name=facility_name)

# Batch Login Route
@app.route('/batch_login', methods=['GET', 'POST'])
def batch_login():
    if request.method == 'POST':
        batch_name = request.form.get('batch')

        if not batch_name:
            return "Batch selection is required.", 400

        db = Database()
        routine = db.execute_query("SELECT * FROM routine WHERE batch_name = %s", (batch_name,), fetch_all=True)
        db.close()

        return render_template('batch_routine.html', routine=routine, batch_name=batch_name)

    return render_template('batch_login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('facility_name', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)