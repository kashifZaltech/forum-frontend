import psycopg2
from psycopg2 import Error
from flask import Flask, render_template
from openai import OpenAI
import requests
import json
import time
import threading

app = Flask(__name__)

# PostgreSQL connection parameters
conn_params = {
    "host": "localhost",
    "dbname": "testdb",
    "user": "postgres",
    "password": "1122",
    "port": 5432
}

# Initialize OpenAI client
client = OpenAI(
    api_key="..."
)

# Askwriter API URL
API_URL = 'http://localhost:5000/markwriter'

# Define a lock for synchronizing file access
file_lock = threading.Lock()

def generate_and_call_askwriter(prompt):
    try:
        # Call askwriter API
        askwriter_data = {'key': 'testkey1', 'topic': prompt}
        response = requests.post(API_URL, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=askwriter_data)
        askwriter_response = response.text
        return askwriter_response
    except Exception as e:
        print("Error calling Askwriter API:", e)
        return None

def write_to_database(prompt, askwriter_response):
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Define your SQL insert query with placeholders for prompt and askwriter_response
        insert_query = """
        INSERT INTO generated_data (prompt, askwriter_response)
        VALUES (%s, %s)
        """
        
        # Execute the insert query with parameters
        cursor.execute(insert_query, (prompt, askwriter_response))
        
        # Commit the transaction
        conn.commit()
        print("Data inserted successfully.")
    except (Exception, Error) as error:
        print("Error while inserting data:", error)
    finally:
        if conn:
            cursor.close()
            conn.close()

def generate_and_store_data():
    prompts = ["Write a Detailed article on Mynt coin and Bit coin", "write an article on impact of cryptocurrency on the global economy"]
    while True:
        for prompt in prompts:
            askwriter_response = generate_and_call_askwriter(prompt)
            if askwriter_response is not None:
                write_to_database(prompt, askwriter_response)
            time.sleep(30*60)

@app.route('/')
def index():
    return "Data is being generated and stored with Askwriter responses every 30 seconds."

@app.route('/posts')
def show_posts():
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Retrieve data from the database
        select_query = """
        SELECT * FROM generated_data
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        # Construct a list of posts
        posts = []
        for row in rows:
            post = {
                "id": row[0],
                "prompt": row[1],
                "askwriter_response": row[2]
            }
            posts.append(post)
        return render_template('post.html', posts=posts)
    except (Exception, Error) as error:
        print("Error while fetching data:", error)
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # Start a separate thread for generating and storing data
    data_thread = threading.Thread(target=generate_and_store_data)
    data_thread.daemon = True
    data_thread.start()
    # Start Flask app
    app.run(debug=True, port=1001)
