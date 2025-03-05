import os
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB Atlas Configuration with improved connection handling
def get_database():
    """
    Establish and return a MongoDB database connection
    """
    try:
        # Parse connection string
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        
        if not connection_string:
            raise ValueError("MongoDB connection string is not set in .env file")
        
        # Create a MongoClient
        client = MongoClient(connection_string)
        
        # Extract database name from connection string
        url_parts = connection_string.split('/')
        database_name = url_parts[-1].split('?')[0] if len(url_parts) > 3 else 'test'
        
        # Get the database
        db = client[database_name]
        
        print(f"Successfully connected to database: {database_name}")
        return db
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

# Initialize database
db = get_database()

# Check if database connection was successful
if db is None:
    raise Exception("Failed to connect to MongoDB. Please check your connection string.")

# Get locations collection
locations_collection = db.locations

@app.route('/')
def index():
    """Render the main location viewer page"""
    return render_template('index.html')

@app.route('/get-latest-location')
def get_latest_location():
    """
    Retrieve the most recent location entry
    """
    try:
        # Find the most recent location entry
        latest_location = locations_collection.find_one(
            sort=[('timestamp', -1)]
        )
        
        if latest_location:
            # Convert ObjectId to string for JSON serialization
            latest_location['_id'] = str(latest_location['_id'])
            latest_location['timestamp'] = latest_location['timestamp'].isoformat()
            
            return jsonify({
                'status': 'success',
                'location': latest_location
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'No locations found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get-all-locations')
def get_all_locations():
    """
    Retrieve all location entries, sorted by timestamp
    """
    try:
        # Find all locations, sorted by timestamp
        all_locations = list(locations_collection.find().sort('timestamp', 1))
        
        # Convert ObjectId to string and format timestamp for each location
        for location in all_locations:
            location['_id'] = str(location['_id'])
            location['timestamp'] = location['timestamp'].isoformat()
        
        return jsonify({
            'status': 'success',
            'locations': all_locations
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Service Worker and Manifest routes
@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)