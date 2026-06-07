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

def fetch_answer_history(author_id: int, limit: int = 50) -> list:
    """Fetch past Q&A history for context injection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, question_text, answer_text, correct_answer, answer_quality
            FROM TBL_answer_list
            WHERE author_id = %s AND answer_quality != 'None'
            ORDER BY insdate DESC
            LIMIT %s
        """
        
        cursor.execute(query, (author_id, limit))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        answer_list = []
        for row in results:
            answer_list.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "correct_answer": row[3],
                "quality": row[4]
            })
        
        return answer_list
    except Exception as e:
        print(f"Error fetching answer history: {e}")
        return []


def save_answer_record(chat_name: str, author_id: int, question_text: str, answer_text: str) -> str:
    """Save a Q&A record to the answer list"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        record_id = f"{author_id}_{int(__import__('time').time() * 1000)}"
        
        query = """
            INSERT INTO TBL_answer_list (id, chat_name, author_id, question_text, answer_text, answer_quality, insdate)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(6))
        """
        
        cursor.execute(query, (record_id, chat_name, author_id, question_text, answer_text, 'None'))
        conn.commit()
        cursor.close()
        conn.close()
        
        return record_id
    except Exception as e:
        print(f"Error saving answer record: {e}")
        raise


def update_answer_quality(record_id: str, quality: str, correct_answer: str = None) -> bool:
    """Update answer quality and correct answer"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if correct_answer:
            query = """
                UPDATE TBL_answer_list
                SET answer_quality = %s, correct_answer = %s
                WHERE id = %s
            """
            cursor.execute(query, (quality, correct_answer, record_id))
        else:
            query = """
                UPDATE TBL_answer_list
                SET answer_quality = %s
                WHERE id = %s
            """
            cursor.execute(query, (quality, record_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error updating answer quality: {e}")
        return False


def get_answer_record(record_id: str) -> dict:
    """Get a specific answer record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, chat_name, question_text, answer_text, correct_answer, answer_quality, insdate
            FROM TBL_answer_list
            WHERE id = %s
        """
        
        cursor.execute(query, (record_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "chat_name": result[1],
                "question": result[2],
                "answer": result[3],
                "correct_answer": result[4],
                "quality": result[5],
                "timestamp": str(result[6]) if result[6] else None
            }
        return None
    except Exception as e:
        print(f"Error fetching answer record: {e}")
        return None


def list_answer_records(author_id: int, limit: int = 100, offset: int = 0) -> tuple:
    """List all answer records for an author with pagination"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        count_query = "SELECT COUNT(*) FROM TBL_answer_list WHERE author_id = %s"
        cursor.execute(count_query, (author_id,))
        total_count = cursor.fetchone()[0]
        
        query = """
            SELECT id, chat_name, question_text, answer_text, correct_answer, answer_quality, insdate
            FROM TBL_answer_list
            WHERE author_id = %s
            ORDER BY insdate DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (author_id, limit, offset))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        records = []
        for row in results:
            records.append({
                "id": row[0],
                "chat_name": row[1],
                "question": row[2],
                "answer": row[3],
                "correct_answer": row[4],
                "quality": row[5],
                "timestamp": str(row[6]) if row[6] else None
            })
        
        return records, total_count
    except Exception as e:
        print(f"Error listing answer records: {e}")
        return [], 0


def delete_answer_record(record_id: str) -> bool:
    """Delete an answer record"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM TBL_answer_list WHERE id = %s"
        cursor.execute(query, (record_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error deleting answer record: {e}")
        return False


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
                    records = json.loads(json_str)
                    # Add author_id to each record if it's missing
                    if isinstance(records, list):
                        for record in records:
                            if 'author_id' not in record or record.get('author_id') is None:
                                record['author_id'] = author_id
                    return records
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
