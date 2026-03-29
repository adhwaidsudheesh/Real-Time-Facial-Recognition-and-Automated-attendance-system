import sqlite3
import os
from datetime import datetime

DB_NAME = "face_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table to store user details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table to store attendance logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Users (name) VALUES (?)', (name,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM Users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return "Unknown"

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM Users')
    results = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in results}

def log_attendance(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Optional: Prevent logging the same person multiple times in a short window (e.g. 5 mins)
    cursor.execute('''
        SELECT timestamp FROM Attendance 
        WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (user_id,))
    
    last_log = cursor.fetchone()
    should_log = True
    
    if last_log:
        last_time = datetime.strptime(last_log[0], '%Y-%m-%d %H:%M:%S')
        if (datetime.now() - last_time).total_seconds() < 300: # 5 minutes cooldown
            should_log = False
            
    if should_log:
        # Use simple string for timestamp for easiest querying
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO Attendance (user_id, timestamp) VALUES (?, ?)', (user_id, current_time))
        conn.commit()
        
    conn.close()
    return should_log

def get_daily_report_data(date_string):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute('SELECT id, name FROM Users')
    users = cursor.fetchall()
    
    report_data = []
    
    for user_id, name in users:
        # Get Earliest and Latest timestamps for this user on this day
        cursor.execute('''
            SELECT MIN(timestamp), MAX(timestamp) 
            FROM Attendance 
            WHERE user_id = ? AND timestamp LIKE ?
        ''', (user_id, f"{date_string}%"))
        
        row = cursor.fetchone()
        
        if row and row[0]: # User has logs today
            check_in_full = row[0]
            check_out_full = row[1]
            
            check_in = check_in_full.split(" ")[1] # extract time part
            check_out = check_out_full.split(" ")[1]
            status = "Present"
            
            # calculate duration
            fmt = '%Y-%m-%d %H:%M:%S'
            t1 = datetime.strptime(check_in_full, fmt)
            t2 = datetime.strptime(check_out_full, fmt)
            
            total_seconds = int((t2 - t1).total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours}h {minutes}m {seconds}s"
            
        else:
            check_in = "N/A"
            check_out = "N/A"
            duration_str = "0h 0m 0s"
            status = "Absent"
            
        report_data.append({
            "User ID": user_id,
            "Name": name,
            "Status": status,
            "Check-In": check_in,
            "Check-Out": check_out,
            "Duration": duration_str
        })
        
    conn.close()
    return report_data

# Initialize the database when this script is imported
init_db()
