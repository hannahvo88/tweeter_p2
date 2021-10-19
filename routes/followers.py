import secrets

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/followers', methods=['GET'])
def Followers_handler():
    try:
        conn = mariadb.connect(
            user=dbcreds.user,
            password=dbcreds.password,
            host=dbcreds.host,
            port=dbcreds.port,
            database=dbcreds.database
        )
        cursor = conn.cursor()
        if xApiToken().checkHasToken():
            if request.method == 'GET':
                data = request.json
                if "userId" in data:
                    userID = data.get("userId")

                    # checks if  integer
                    if not str(userID).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)
                    cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [userID])
                    check_id_valid = cursor.fetchone()[0]

                    if check_id_valid == 1:
                        cursor.execute("SELECT id, email, username, bio, birthdate FROM user INNER JOIN follow ON user.id = follow.follower WHERE follow.followed=?", [userID])

                        # this will extract row headers
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        json_data = []
                        for result in rv:
                            json_data.append(dict(zip(row_headers, result)))

                        return jsonify(json_data), 200
                    else:
                        return jsonify({
                            'message': "user  not found"
                        }), 404
                else:
                    return jsonify({
                        'message': "user id not found"
                    }), 400

        else:
            return Response("X-Api-Key not found", mimetype='application/json', status=400)
    
    except mariadb.OperationalError:
        print("There seems to be a connection issue!")
    except mariadb.ProgrammingError:
        print("Apparently you do not know how to code")
    except mariadb.IntergrityError:
        print("Error with DB integrity, most likely consraint failure")
    except:
        print("Opps! Somthing went wrong")
    finally:
        if (cursor != None):
            cursor.close()
        else:
            print("No cursor to begin with.")
        
        if (conn != None):
            conn.rollback()
            conn.close()
        else:
            print("No connection!")
