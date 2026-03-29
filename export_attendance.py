import csv
import os
import sys
import subprocess
from datetime import datetime
import database

def get_today_date_str():
    return datetime.now().strftime('%Y-%m-%d')

def generate_csv_report(date_string=None):
    if not date_string:
        date_string = get_today_date_str()
        
    data = database.get_daily_report_data(date_string)
    
    if not data:
        print("No users to report on.")
        return None
        
    filename = f"AttendanceReport_{date_string}.csv"
    
    # Headers based on our database return format
    headers = ["User ID", "Name", "Status", "Check-In", "Check-Out", "Duration"]
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        
        # Sort so Present users appear first, then by name
        data.sort(key=lambda x: (x["Status"] == "Absent", x["Name"]))
        
        for row in data:
            writer.writerow(row)
            
    print(f"Success: Exported daily attendance report to {filename}")
    
    # Automatically open the generated Excel file
    try:
        os.startfile(filename) # Windows
    except AttributeError:
        # Fallback for Mac/Linux
        if sys.platform == "darwin":
            subprocess.call(["open", filename])
        else:
            subprocess.call(["xdg-open", filename])
            
    return filename

if __name__ == "__main__":
    generate_csv_report()
