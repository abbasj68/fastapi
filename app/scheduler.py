from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from database import SessionLocal
from models import TokenBlocklist

def cleanup_expired_tokens():
    db=SessionLocal()
    try:
        expiration_time = datetime.utcnow() - timedelta(days=30)
        deleted_count = db.query(TokenBlocklist).filter(TokenBlocklist.created_at < expiration_time).delete()
        db.commit()
        if deleted_count > 0:
            print(f"[scheduler] Deleted {deleted_count} expired token.")
    except Exception as e:
        print(f"[scheduler Error] {e}") 
    finally:
        db.close()
        
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_expired_tokens, "interval", days=1)
    scheduler.start()