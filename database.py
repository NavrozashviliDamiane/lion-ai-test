import pymysql
import json
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        raise

def fetch_author_data(author_id: int) -> list:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"CALL PROC_GET_JSON({author_id})")
        
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            json_str = result[0][0]
            if isinstance(json_str, str):
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as je:
                    print(f"JSON decode error at position {je.pos}: {je.msg}")
                    print(f"Total length: {len(json_str)}")
                    print(f"Context around error: ...{json_str[max(0, je.pos-100):je.pos+100]}...")
                    
                    truncated_str = json_str[:je.pos]
                    
                    last_brace = truncated_str.rfind('}')
                    if last_brace != -1:
                        truncated_str = truncated_str[:last_brace+1]
                    
                    if truncated_str.rstrip().endswith(','):
                        truncated_str = truncated_str.rstrip()[:-1]
                    
                    truncated_str = truncated_str.rstrip() + ']'
                    
                    try:
                        print("Attempting to parse truncated JSON...")
                        parsed = json.loads(truncated_str)
                        print(f"Successfully parsed {len(parsed)} records from truncated JSON")
                        return parsed
                    except Exception as trunc_error:
                        print(f"Could not parse truncated JSON: {trunc_error}")
                        print(f"Truncated string ends with: ...{truncated_str[-200:]}")
                        raise je
            return json_str if isinstance(json_str, list) else []
        return []
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        raise
