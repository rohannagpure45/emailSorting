import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'agent_performance.db')

def init_db():
    """Initialize the database with required tables"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create table for email processing records
    c.execute('''
    CREATE TABLE IF NOT EXISTS email_processing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        email_id TEXT,
        subject TEXT,
        category TEXT,
        confidence REAL,
        processing_time REAL,
        success INTEGER
    )
    ''')
    
    # Create table for daily summary statistics
    c.execute('''
    CREATE TABLE IF NOT EXISTS daily_stats (
        date TEXT PRIMARY KEY,
        total_processed INTEGER,
        categories TEXT,
        avg_confidence REAL,
        avg_processing_time REAL,
        success_rate REAL
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at: {DB_PATH}")

def log_email_processing(email_id, subject, category, confidence, processing_time, success=True):
    """Log a processed email's data"""
    # Ensure DB is initialized
    if not os.path.exists(DB_PATH):
        init_db()
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
    INSERT INTO email_processing 
    (timestamp, email_id, subject, category, confidence, processing_time, success)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        email_id,
        subject,
        category,
        confidence,
        processing_time,
        1 if success else 0
    ))
    
    conn.commit()
    conn.close()

def update_daily_stats():
    """Update or create daily statistics"""
    # Ensure DB is initialized
    if not os.path.exists(DB_PATH):
        init_db()
        return  # No data to process yet
    
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get today's data
    c.execute('''
    SELECT 
        COUNT(*) as total,
        GROUP_CONCAT(DISTINCT category) as categories,
        AVG(confidence) as avg_conf,
        AVG(processing_time) as avg_time,
        SUM(success) * 100.0 / COUNT(*) as success_rate
    FROM email_processing
    WHERE date(timestamp) = date(?)
    ''', (today,))
    
    result = c.fetchone()
    
    if result and result[0] > 0:
        # Update or insert daily stats
        c.execute('''
        INSERT OR REPLACE INTO daily_stats
        (date, total_processed, categories, avg_confidence, avg_processing_time, success_rate)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            today,
            result[0],  # total
            result[1],  # categories
            result[2],  # avg_confidence
            result[3],  # avg_processing_time
            result[4]   # success_rate
        ))
        
    conn.commit()
    conn.close() 