from flask import Flask, request, jsonify

# from flask_marshmallow import marshmalllow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))


@app.route("/")
def entry():
    return "working"


if __name__ == "__main__":
    app.run(debug=True)
