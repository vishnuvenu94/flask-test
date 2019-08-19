from flask import Flask, request, jsonify
import json
from waitress import serve

# from flask_marshmallow import marshmalllow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
PORT = 8080


@app.route("/")
def entry():
    return "working"


@app.route("/events", methods=['POST'])
def handleEvents():
    print(request)
    file = open("myfile.txt", "w+")
    file.write(json.dumps(request.json))
    file.close()
    return json.dumps(request.json)


if __name__ == "__main__":
    # app.run(debug=True)
    serve(app, listen='*:{}'.format(str(PORT)))
