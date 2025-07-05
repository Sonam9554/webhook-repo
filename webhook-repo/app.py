from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))  # use dotenv or hardcode for now
db = client.github_events
collection = db.events

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Determine action type
    event = request.headers.get('X-GitHub-Event')
    parsed = {}

    if event == "push":
        parsed = {
            "type": "push",
            "author": data["pusher"]["name"],
            "to_branch": data["ref"].split('/')[-1],
            "timestamp": datetime.utcnow()
        }

    elif event == "pull_request":
        pr = data["pull_request"]
        parsed = {
            "type": "pull_request",
            "author": pr["user"]["login"],
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": datetime.utcnow()
        }

    elif event == "merge":
        # GitHub doesn't send separate "merge" event. Handle in `pull_request` if `merged == true`
        pass

    if parsed:
        collection.insert_one(parsed)

    return '', 204

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort("timestamp", -1).limit(20))
    for e in events:
        e["_id"] = str(e["_id"])
        e["timestamp"] = e["timestamp"].strftime("%d %B %Y - %I:%M %p UTC")
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
