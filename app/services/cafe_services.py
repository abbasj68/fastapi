from sqlalchemy import text
from sqlalchemy.orm import Session

def get_nearest_cafes(db : Session, user_lat: float, user_lon: float, limit: int=20):
    query = text(f"""
        SELECT id,name,
                ST_Y(location) AS latitude,
                ST_X(location) AS longitude,
                ST_Distance_Sphere(location, ST_GeomFromText(:point,4326)) AS distance
        FROM cafes
        WHERE ST_Distance_Sphere(location, ST_GeomFromText(:point, 4326)) > 0
        ORDER BY distance ASC
        LIMIT {limit}  
        """)
    point = f"POINT({user_lon} {user_lat})"
    result = db.execute(query , {"point":point}).mappings().all()
    
    categories = {
        "near" : [],
        "medium" : [],
        "far" : []
    }
    
    for cafe in result:
        if cafe["distance"] <= 1000:
            categories["near"].append(cafe)
        elif cafe["distance"] <= 5000:
            categories["medium"].append(cafe)
        else:
            categories["far"].append(cafe)
            
    return {"cafes":categories}
