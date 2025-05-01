#!/usr/bin/env python3
import os
import sys
import subprocess
import sqlite3

def check_database():
    """Check if the database exists and has data."""
    db_path = os.path.join(os.path.dirname(__file__), "dashboard", "agent_performance.db")
    
    if not os.path.exists(db_path):
        print("Database not found. Would you like to generate sample data? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            sample_data_script = os.path.join(os.path.dirname(__file__), "dashboard", "generate_sample_data.py")
            subprocess.run([sys.executable, sample_data_script])
            return True
    else:
        # Check if there's any data in the database
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM email_processing")
            count = c.fetchone()[0]
            conn.close()
            
            if count == 0:
                print("Database exists but has no data. Would you like to generate sample data? (y/n)")
                choice = input().strip().lower()
                if choice == 'y':
                    sample_data_script = os.path.join(os.path.dirname(__file__), "dashboard", "generate_sample_data.py")
                    subprocess.run([sys.executable, sample_data_script])
        except sqlite3.Error:
            # Tables might not exist
            print("Database found but tables may not be initialized.")
            print("Would you like to generate sample data? (y/n)")
            choice = input().strip().lower()
            if choice == 'y':
                sample_data_script = os.path.join(os.path.dirname(__file__), "dashboard", "generate_sample_data.py")
                subprocess.run([sys.executable, sample_data_script])
    
    return True

def main():
    # Path to the dashboard app
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    
    # Check if the dashboard file exists
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard file not found at {dashboard_path}")
        print("Please make sure you're running this script from the correct directory.")
        sys.exit(1)
    
    # Check database status
    check_database()
    
    print("\nStarting the Email Sorting Dashboard...")
    print("Press Ctrl+C to stop the dashboard.\n")
    
    try:
        # Run the Streamlit app
        subprocess.run(["streamlit", "run", dashboard_path], check=True)
    except FileNotFoundError:
        print("\nError: Streamlit not found. Please install it with:")
        print("pip install streamlit\n")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nError running the dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDashboard stopped by user.")
    
if __name__ == "__main__":
    main() 