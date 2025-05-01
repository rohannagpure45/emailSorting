#!/usr/bin/env python3
"""
Script to generate sample data for testing the email sorting dashboard.
"""
import os
import sqlite3
import random
from datetime import datetime, timedelta
import sys

# Add the parent directory to the path so we can import the dashboard module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.database import init_db, update_daily_stats, DB_PATH

def generate_sample_data(num_records=50):
    """Generate sample data for the dashboard."""
    # Initialize the database
    init_db()
    
    # Open connection
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Sample data
    categories = [
        'work', 'personal', 'promotional', 'finance', 'travel', 
        'shopping', 'social', 'news', 'education', 'events', 
        'updates', 'legal', 'other'
    ]
    
    subjects = [
        'Project Update from Team', 'Hello from John', 'Special Offer: 50% off!',
        'Your Monthly Statement', 'Flight Confirmation: Trip to Paris',
        'Order #12345 Has Shipped', 'New Friend Request', 'Breaking News Alert',
        'Course Registration Confirmation', 'Event Invitation: Annual Party',
        'System Update Required', 'Terms of Service Update', 'Meeting Notes'
    ]
    
    senders = [
        'john@example.com', 'team@company.com', 'marketing@store.com',
        'bank@finance.com', 'travel@airline.com', 'orders@shop.com',
        'notifications@social.com', 'news@media.com', 'support@edu.com',
        'events@company.com', 'system@updates.com', 'legal@company.com'
    ]
    
    # Generate random data
    print(f"Generating {num_records} sample email records...")
    for i in range(num_records):
        # Pick random category and matching subject/sender
        idx = i % len(categories)
        category = categories[idx]
        subject = subjects[idx % len(subjects)]
        sender = senders[idx % len(senders)]
        
        # Random date within the last 14 days
        days_ago = random.randint(0, 14)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        # Random confidence and processing times
        confidence = random.uniform(0.6, 0.98)
        processing_time = random.uniform(0.5, 5.0)
        
        # Randomize success (90% success rate)
        success = 1 if random.random() < 0.9 else 0
        
        # Insert record
        c.execute('''
        INSERT INTO email_processing 
        (timestamp, email_id, subject, category, confidence, processing_time, success)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            f"sample_email_{i}",
            f"{subject} #{i}",
            category,
            confidence,
            processing_time,
            success
        ))
    
    # Commit changes
    conn.commit()
    
    # Update daily statistics
    print("Updating daily statistics...")
    update_daily_stats()
    
    # Close connection
    conn.close()
    
    print("Sample data generation complete!")
    print(f"Database location: {DB_PATH}")

if __name__ == "__main__":
    # Get the number of records from command line argument if provided
    num_records = 50
    if len(sys.argv) > 1:
        try:
            num_records = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of records: {sys.argv[1]}. Using default (50).")
    
    generate_sample_data(num_records) 