from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from marshmallow import fields, Schema, ValidationError
import mysql.connector
from mysql.connector import Error
from password import my_password
from datetime import datetime, time

app = Flask(__name__)
ma = Marshmallow(app)

# MembersSchema using Marshmallow
class MembersSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    name = fields.String(required=True)
    age = fields.Int(required=True)

# Initialize schema
members_schema = MembersSchema()
members_schemas = MembersSchema(many=True)

def get_db_connection():
    db_name = "fitness_center_db"
    user = "root"
    password = my_password
    host = "localhost"

    try:
        conn = mysql.connector.connect(
            database=db_name,
            user=user,
            password=password,
            host=host
        )
        print("Connected to MySQL database successfully.")
        return conn
    
    except Error as e:
        print(f"Error: {e}")
        return None

@app.route('/members', methods=['POST'])
def add_member():
    try:
        members_data = members_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO members (name, age) VALUES (%s, %s)"
        cursor.execute(query, (members_data['name'], members_data['age']))
        conn.commit()
        return jsonify({"message": "Member added successfully"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/members', methods=['GET'])
def get_all_members():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM members"
        cursor.execute(query)
        members = cursor.fetchall()
        return jsonify(members_schemas.dump(members))
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM members WHERE id = %s"
        cursor.execute(query, (member_id,))
        member = cursor.fetchone()
        
        if member:
            return jsonify(members_schema.dump(member))
        else:
            return jsonify({"error": "Member not found"}), 404
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Define WorkoutSessionsSchema using Marshmallow
class WorkoutSessionsSchema(ma.Schema):
    session_id = fields.Int(dump_only=True)
    member_id = fields.Int(required=True)
    session_date = fields.Date(required=True)
    session_time = fields.Time(required=True)
    activity = fields.String(required=True)

# Initialize schema objects
workout_sessions_schema = WorkoutSessionsSchema()
workout_sessions_schemas = WorkoutSessionsSchema(many=True)

# Route to schedule a new workout session
@app.route('/workoutsessions/add', methods=['POST'])
def add_workout():
    try:
        workout_data = workout_sessions_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO workoutsessions (member_id, session_date, session_time, activity) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (workout_data['member_id'], workout_data['session_date'], workout_data['session_time'], workout_data['activity']))
        conn.commit()
        return jsonify({"message": "Workout added successfully"}), 201
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/workoutsessions/<int:id>', methods=['PUT'])
def update_workout(id):
    try:
        data = workout_sessions_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        query = "UPDATE workoutsessions SET session_date = %s, session_time = %s, activity = %s WHERE session_id = %s"
        cursor.execute(query, (data['session_date'], data['session_time'], data['activity'], id))
        conn.commit()
        return jsonify({"message": "Workout session updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/workoutsessions/<int:id>', methods=['GET'])
def get_workout(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM workoutsessions WHERE session_id = %s"
        cursor.execute(query, (id,))
        workout = cursor.fetchone()
        
        if workout:
            workout['session_time'] = datetime.strptime(workout['session_time'], '%H:%M:%S').time()
            return jsonify(workout_sessions_schema.dump(workout))
        else:
            return jsonify({"message": "Workout session not found"}), 404
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/workoutsessions/member/<int:member_id>', methods=['GET'])
def get_workouts_for_member(member_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM workoutsessions WHERE member_id = %s"
        cursor.execute(query, (member_id,))
        workouts = cursor.fetchall()
        return jsonify(workout_sessions_schemas.dump(workouts))
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
