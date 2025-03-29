from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import cv2
import numpy as np
import os
import base64
import mysql.connector
import re
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------- Database Connection ----------------
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Milan@721166',
        database='login_system'
    )
@app.route('/')
def home():
    return render_template('index.html')
# Admin Panel
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required."})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({"success": True, "message": "Login successful!"})
        else:
            return jsonify({"success": False, "message": "Invalid username or password."})

    return render_template('admin_login.html')

# Admin Dashboard Route
@app.route('/admin/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM facilities")
        facilities = cursor.fetchall()
        cursor.execute("SELECT * FROM batches")
        batches = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_dashboard.html', facilities=facilities, batches=batches)
    return redirect(url_for('admin_login'))

# Add Facility Route
@app.route('/add_facility', methods=['POST'])
def add_facility():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        facility_name = request.form['facility_name']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO facilities (facility_name) VALUES (%s)", (facility_name,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/delete_facility/<int:facility_id>', methods=['POST'])
def delete_facility(facility_id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM facilities WHERE id = %s", (facility_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

# Add Batch Route
@app.route('/add_batch', methods=['POST'])
def add_batch():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        batch_name = request.form['batch_name']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO batches (batch_name) VALUES (%s)", (batch_name,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

# Delete Batch Route
@app.route('/delete_batch/<int:batch_id>', methods=['POST'])
def delete_batch(batch_id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM batches WHERE id = %s", (batch_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

# Faculty Login Route
@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    return render_template('faculty_login.html')

# Batch Login Route
@app.route('/batch_login', methods=['GET', 'POST'])
def batch_login():
    return render_template('batch_login.html')

if __name__ == '__main__':
    app.run(debug=True)