from flask import Flask, render_template, request, abort, jsonify, make_response
from dotenv import load_dotenv
import os
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# get environment variables
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

## implement GET /
@app.get('/')
def index():
    print('request method is: ' + request.method)
    if request.method == 'GET':
        print('200 OK. Serving boogle.html')
        return make_response(render_template('boogle.html'), 200)
    else:
        print("ERROR: Bad Request (not 'GET')")
        return abort(400)


## implement GET /jsontest
@app.route('/jsontest')
def json():
    print('routing to /jsontest...\nrequest method is: ' + request.method)
    if request.method == 'GET':
        data = {"data" : "I am in CSE190/CSE291!"}
        return make_response(jsonify(data), 200)
    else:
        print("ERROR: Bad Request (not 'GET')")
        return abort(400)

if __name__ == "__main__":
    #replaced host="0.0.0.0" with internal IP address of vm instance 10.138.0.3
    app.run(host="10.138.0.3", port="8000")
