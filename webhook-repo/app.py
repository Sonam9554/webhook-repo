from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# Connect to MongoDB (You can hardcode this if .env fails)
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client.github_events
collection = db.events

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event = request.headers.get('X-GitHub-Event')

    print(f"Received event: {event}")

    parsed = {}

    try:
        if event == "push":
            parsed = {
                "type": "push",
                "author": data.get("pusher", {}).get("name", "unknown"),
                "to_branch": data.get("ref", "").split("/")[-1],
                "timestamp": datetime.utcnow()
            }

        elif event == "pull_request":
            pr = data.get("pull_request", {})
            parsed = {
                "type": "pull_request",
                "author": pr.get("user", {}).get("login", "unknown"),
                "from_branch": pr.get("head", {}).get("ref", "unknown"),
                "to_branch": pr.get("base", {}).get("ref", "unknown"),
                "merged": pr.get("merged", False),
                "timestamp": datetime.utcnow()
            }

        if parsed:
            collection.insert_one(parsed)
            print("Stored event:", parsed)
        else:
            print("Unrecognized or incomplete event data.")

    except Exception as e:
        print("Error parsing webhook:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify({"status": "success"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort("timestamp", -1).limit(20))
    for e in events:
        e["_id"] = str(e["_id"])
        e["timestamp"] = e["timestamp"].strftime("%d %B %Y - %I:%M %p UTC")
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
