from sqlalchemy import create_engine, text

# آدرس اتصال — پورت رو اگر تغییر ندادی بذار 3306
DATABASE_URL = "mysql+pymysql://root:Abbasj%231374@localhost:3306/test"

# ساخت Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

try:
    # باز کردن اتصال
    with engine.connect() as conn:
        result = conn.execute(text("SELECT VERSION()"))
        version = result.scalar()
        print(f"✅ اتصال موفق — نسخه MySQL: {version}")

except Exception as e:
    print(f"❌ خطا در اتصال: {e}")
