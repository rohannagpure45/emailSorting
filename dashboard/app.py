import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from datetime import datetime, timedelta
import sys

# Make sure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database functions
from dashboard.database import init_db, log_email_processing, update_daily_stats

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'agent_performance.db')

# Initialize database
init_db()

def get_connection():
    """Get a connection to the database with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_data():
    """Load data from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Initialize data dictionaries
    data = {
        'recent_emails': pd.DataFrame(),
        'daily_stats': pd.DataFrame(),
        'category_dist': pd.DataFrame(),
        'summary': {
            'total_processed': 0,
            'avg_confidence': 0,
            'avg_time': 0,
            'success_rate': 0
        }
    }
    
    try:
        # Get recent email processing logs
        cursor.execute('''
        SELECT * FROM email_processing 
        ORDER BY timestamp DESC LIMIT 100
        ''')
        rows = cursor.fetchall()
        
        if rows:
            data['recent_emails'] = pd.DataFrame([dict(row) for row in rows])
            
            # Calculate summary metrics
            cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(confidence) as avg_conf,
                AVG(processing_time) as avg_time,
                SUM(success) * 100.0 / COUNT(*) as success_rate
            FROM email_processing
            ''')
            summary = cursor.fetchone()
            
            if summary:
                data['summary'] = {
                    'total_processed': summary['total'],
                    'avg_confidence': summary['avg_conf'],
                    'avg_time': summary['avg_time'],
                    'success_rate': summary['success_rate']
                }
            
            # Get daily statistics for trend visualization
            cursor.execute('''
            SELECT * FROM daily_stats
            ORDER BY date DESC
            LIMIT 30
            ''')
            rows = cursor.fetchall()
            if rows:
                data['daily_stats'] = pd.DataFrame([dict(row) for row in rows])
                data['daily_stats']['date'] = pd.to_datetime(data['daily_stats']['date'])
                data['daily_stats'] = data['daily_stats'].sort_values('date')
            
            # Get category distribution
            cursor.execute('''
            SELECT 
                category,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM email_processing
            GROUP BY category
            ORDER BY count DESC
            ''')
            rows = cursor.fetchall()
            if rows:
                data['category_dist'] = pd.DataFrame([dict(row) for row in rows])
    
    except sqlite3.Error as e:
        st.error(f"Error loading data: {e}")
        if str(e).find("no such table") >= 0:
            st.info("Database tables not found. Initializing database...")
            init_db()
    
    finally:
        conn.close()
    
    return data

def insert_test_data():
    """Insert test data for demonstration purposes"""
    st.info("Generating test data for the dashboard...")
    
    # Check if sample data generator script exists
    sample_script = os.path.join(os.path.dirname(__file__), 'generate_sample_data.py')
    if os.path.exists(sample_script):
        import subprocess
        subprocess.run([sys.executable, sample_script, "50"])
        st.success("Test data generated successfully!")
        st.info("Refresh the page to see the data.")
    else:
        # Fallback: generate a few records directly
        conn = get_connection()
        c = conn.cursor()
        
        # Sample categories and data
        categories = ['work', 'personal', 'promotional', 'finance', 'social']
        
        # Generate 10 test records
        for i in range(10):
            import random
            category = random.choice(categories)
            confidence = random.uniform(0.7, 0.98)
            processing_time = random.uniform(0.5, 3.0)
            
            # Insert record
            log_email_processing(
                f"test_email_{i}",
                f"Test Subject {i}",
                category,
                confidence,
                processing_time,
                success=True
            )
        
        # Update stats
        update_daily_stats()
        st.success("Basic test data generated. Refresh the page to see it.")
    
    return

def main():
    # Configure the app
    st.set_page_config(
        page_title="Email Sorting Agent Dashboard",
        page_icon="📈",
        layout="wide"
    )
    
    # Header
    st.title("📊 Email Sorting Agent Performance Dashboard")
    st.markdown("Monitor the performance and statistics of your email sorting agent.")
    
    # Load data
    data = load_data()
    
    # Check if we have any data
    if len(data['recent_emails']) == 0:
        st.warning("No email processing data found in the database.")
        if st.button("Generate Sample Data"):
            insert_test_data()
        st.stop()
    
    # Add a refresh button
    col_refresh = st.columns([0.8, 0.2])
    with col_refresh[1]:
        if st.button("🔄 Refresh Data"):
            st.experimental_rerun()
    
    # Summary metrics
    st.subheader("Performance Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Emails Processed", f"{int(data['summary']['total_processed']):,}")
    with col2:
        st.metric("Avg. Confidence Score", f"{data['summary']['avg_confidence']:.2f}")
    with col3:
        st.metric("Avg. Processing Time", f"{data['summary']['avg_time']:.2f}s")
    with col4:
        st.metric("Success Rate", f"{data['summary']['success_rate']:.1f}%")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["📈 Daily Performance", "📊 Category Analysis", "📃 Recent Emails"])
    
    # Tab 1: Daily Performance
    with tab1:
        st.subheader("Daily Performance Trends")
        
        if len(data['daily_stats']) > 0:
            # Create line charts for daily metrics
            fig = px.line(
                data['daily_stats'], 
                x='date', 
                y=['total_processed', 'avg_confidence', 'avg_processing_time', 'success_rate'],
                labels={'value': 'Metric Value', 'date': 'Date', 'variable': 'Metric'},
                title="Daily Performance Metrics"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No daily statistics available yet. Process more emails to generate daily trends.")
    
    # Tab 2: Category Analysis
    with tab2:
        st.subheader("Email Category Distribution")
        
        if len(data['category_dist']) > 0:
            # Create a bar chart for category distribution
            fig1 = px.bar(
                data['category_dist'], 
                x='category', 
                y='count',
                color='avg_confidence',
                color_continuous_scale='Viridis',
                labels={'count': 'Number of Emails', 'category': 'Category', 'avg_confidence': 'Avg. Confidence'},
                title="Email Distribution by Category"
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Display category details in a table
            st.subheader("Category Details")
            st.dataframe(data['category_dist'], use_container_width=True)
        else:
            st.info("No category distribution data available yet.")
    
    # Tab 3: Recent Emails
    with tab3:
        st.subheader("Recently Processed Emails")
        
        if len(data['recent_emails']) > 0:
            # Add filtering options
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                if len(data['recent_emails']['category'].unique()) > 0:
                    selected_category = st.selectbox(
                        "Filter by Category",
                        options=["All"] + sorted(data['recent_emails']['category'].unique().tolist())
                    )
            
            with filter_col2:
                date_range = st.radio(
                    "Time Range",
                    options=["All", "Today", "Last 7 Days"]
                )
            
            # Apply filters
            filtered_df = data['recent_emails'].copy()
            
            if selected_category != "All":
                filtered_df = filtered_df[filtered_df['category'] == selected_category]
            
            if date_range != "All":
                filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])
                if date_range == "Today":
                    today = datetime.now().date()
                    filtered_df = filtered_df[filtered_df['timestamp'].dt.date == today]
                elif date_range == "Last 7 Days":
                    week_ago = datetime.now() - timedelta(days=7)
                    filtered_df = filtered_df[filtered_df['timestamp'] >= week_ago]
            
            # Display the filtered dataframe
            st.dataframe(
                filtered_df[['timestamp', 'email_id', 'subject', 'category', 
                           'confidence', 'processing_time', 'success']],
                use_container_width=True
            )
        else:
            st.info("No recently processed emails available.")

if __name__ == "__main__":
    main() 