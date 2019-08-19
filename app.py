from flask import Flask, request, jsonify
import json

# from flask_marshmallow import marshmalllow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))


@app.route("/")
def entry():
    return "working"


@app.route("/events", methods=['POST'])
def handleEvents():
    print(request)
    return json.dumps(request.json)


if __name__ == "__main__":
    app.run(debug=True)
