from flask import Flask, redirect, render_template, request, abort, jsonify, make_response
from flask_socketio import SocketIO, emit
from uuid import uuid4, UUID
import os
#from mysqlx import Row
import datetime
import psycopg2

app = Flask(__name__)
socketio = SocketIO(app)

## Connect database
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = os.environ["B00-s3rv3r"]
DB_HOST = "127.0.0.1"
DB_PORT = "5430"

try:
    conn = psycopg2.connect(database=DB_NAME,
                            user=DB_USER,
                            password=DB_PASS,
                            host=DB_HOST,
                            port=DB_PORT)
    print("break1")
    boogledb = conn.cursor()
    print("Database connected successfully")
    print("break2")
except:
    print("Database not connected successfully")
    print("break3")
    

@socketio.on('disconnect')
def disconnect_server():
    conn.close()

## implement GET /
@app.get('/')
def index():
    print('request method is: ' + request.method)
    if request.method == 'GET':
        print('200 OK. Serving boogle.html')

        response = make_response(render_template('boogle.html'))

        # check for existing cookie
        user_id = str(request.cookies.get('boogle_id'))
        
        if user_id is None:
            # create persistent cookie: name=boogle_id, key=uuid4, expires=1month, samesite=lax, secure=false
            new_id = str(uuid4())
            response.set_cookie('boogle_id', value=new_id, path='/', expires='Sat, 31 Oct 2026 11:59:00 PST',
                                secure=False, samesite='lax')

            print('\nnew user inserted into client with value: ' + new_id + '\n')

            # add cookie to database
            boogledb.execute("INSERT INTO clients (client_id) VALUES (%s);", (new_id, ))
        else:
            try:
                print('\ncookie exists with id: ' + user_id + '\n')
                print('\n updating user in clients to last_seen\n')
                
                # update last_seen for user's cookie
                boogledb.execute("UPDATE clients SET last_seen = DEFAULT WHERE client_id = %s;", (user_id, ))
            except:
                # in case there is a cookie but no database entry for it
                response.set_cookie('boogle_id', value=user_id, path='/', expires='Sat, 31 Oct 2026 11:59:00 PST',
                                                secure=False, samesite='lax')
                boogledb.execute("INSERT INTO clients (client_id) VALUES (%s);", (user_id, ))

        # record request to requests table
        #user_id = request.cookies.get('boogle_id')
        u_ip = request.remote_addr
        u_referer = request.referrer
        u_path = "/"
        boogledb.execute("INSERT INTO requests (client_id, ip, referer, path) VALUES (%s, %s, %s, %s);", (user_id, u_ip, u_referer, u_path))
        
        # add changes to boogledb
        conn.commit()
        return response, 200
    else:
        print("ERROR: Bad Request (not 'GET')")
        return abort(400)

## implement GET /search
@app.route('/search')
def search():
    print('\nYou\'ve searched something')
    query = request.args.get('q', type=str)
    user_id = str(request.cookies.get('boogle_id'))

    # check that query isn't empty or all whitespace
    if (query is not None) and (query.isspace() is False):
        print('got search: ' + query + '\n')

        ## store query in database
        boogledb.execute("INSERT INTO searches (client_id, query) VALUES (%s, %s);", (user_id, query))

        ## update clients last_seen
        boogledb.execute("UPDATE clients SET last_seen = DEFAULT WHERE client_id = %s;", (user_id, ))
    else:
        print ('invalid query\n')

    # record request to requests table
    u_ip = request.remote_addr
    u_referer = request.referrer
    u_path = "/"
    boogledb.execute("INSERT INTO requests (client_id, ip, referer, path) VALUES (%s, %s, %s, %s);", (user_id, u_ip, u_referer, u_path))     

    # add changes to boogledb
    conn.commit()

    return redirect(location='/', code=303)

## implement GET /api/history
@app.route('/api/history')
def history():
    # get all searches made by client (in reverse order chronologically)
    user_id = str(request.cookies.get('boogle_id'))

    #try:
    boogledb.execute("SELECT json_build_object('client_id', %s, 'searches', boogleschema.get_searches_by_id(%s));", (user_id, user_id))
    client_searches = boogledb.fetchone()[0]

    # return as json
    return make_response(jsonify(client_searches), 200)
    #except:
    #    return make_response('error fetching searches', 404)
    

## implement GET /dump
@app.route('/dump')
def dump():
    # get all requests from all clients in array format
    #try:
    boogledb.execute("SELECT boogleschema.dump_data();")
    dump = boogledb.fetchone()[0]

    # return as json
    return make_response(jsonify(dump), 200)
    #except:
        #conn.close()
    #    return make_response('error fetching searches', 404)

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
    #replaced host="0.0.0.0" with external IP address of vm instance
    print("in main!")
    app.run(host="0.0.0.0", port="8000", debug=True)

# close connection to boogle database
#conn.close()
