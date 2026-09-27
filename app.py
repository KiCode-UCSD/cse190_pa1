from flask import Flask, render_template, request, abort, jsonify, make_response
from markupsafe import escape
app = Flask(__name__)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000")

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

