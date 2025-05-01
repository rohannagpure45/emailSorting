from .database import init_db, log_email_processing, update_daily_stats

# Initialize the database when module is imported
init_db()

__all__ = [
    'init_db',
    'log_email_processing',
    'update_daily_stats'
] 