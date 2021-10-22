import json
import secrets

import mariadb
from flask import Response, request, jsonify

import dbcreds
from apptoken import xApiToken
from routes import app


def required_params(required):
    json = request.get_json()
    missing = [r for r in required.keys()
        if r not in json]
    print(len(missing))
    if len(missing) > 0:
        return {
            "status": False,
            "data": missing
        }
    else:
        return {
            "status": True,
            "data": []
        }


@app.route('/api/users', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def api_users():
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
                data = request.args
                userId = data.get("userId")
                if "userId" != data:
                    cursor.execute("SELECT id, email, username FROM user")

                    # this will extract row headers
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []

                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    res = json_data
                elif "userId" in data:
                
                    if userId .isdigit():
                        cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [userId])
                        id_valid = cursor.fetchone()[0]
                        if id_valid == 1:
                            cursor.execute(f"SELECT id, email, username FROM user WHERE id=?",[userId])

                            # this will extract row headers
                            row_headers = [x[0] for x in cursor.description]
                            rv = cursor.fetchall()
                            json_data = []
                            for result in rv:
                                json_data.append(dict(zip(row_headers, result)))

                            res = json_data
                        else:
                            return jsonify({
                                'message': "User id does not found"
                            }), 400
                    else:
                        return jsonify({
                            'message': "Invalid Request"
                        }), 400
                else:
                    return jsonify({
                        'message': "Invalid Request"
                    }), 400

                return jsonify(res), 200

            elif request.method == 'POST':
                data = request.json
                email = data.get("email")
                username = data.get("username")
                password = data.get("password")
                bio = data.get("bio")
                birthdate = data.get("birthdate")

                validated = required_params({
                    "email": "",
                    "username": "",
                    "birthdate": "",
                    "bio": "",
                    "password": ""
                })

                if not validated['status']:
                    return jsonify({
                        "message": "Request JSON is missing some required params",
                        "missing": validated['data']
                    })
                else:

                    # check email exists
                    cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE email=?)", [email])
                    check_email_exists = cursor.fetchone()[0]

                    if check_email_exists == 1:
                        return jsonify({
                            "message": "Email already exists"
                        }), 400

                    # check username exists
                    cursor.execute("SELECT EXISTS(SELECT username FROM user WHERE username=?)", [username])
                    check_username_exists = cursor.fetchone()[0]

                    if check_username_exists == 1:
                        return jsonify({
                            'message': "Username already exists"
                        }), 400

                    # insert data
                    cursor.execute("INSERT INTO user(email, username, password, bio, birthdate), VALUES(?,?,?,?,?)", [email], [username], [password], [bio], [birthdate])
                    conn.commit()
                    cursor.execute("SELECT id FROM user WHERE email=?", [email])
                    user_id = cursor.fetchone()[0]

                    login_token = secrets.token_hex(16)
                    cursor.execute("INSERT INTO user_session(user_id, login_token) VALUES(?,?)", [user_id, login_token])
                    conn.commit()

                    cursor.execute("SELECT id, email, username, bio, birthdate FROM user WHERE id=?", [user_id])
                    user = cursor.fetchone()

                    resp = {
                        "userId": user[0],
                        "email": user[1],
                        "username": user[2],
                        "bio": user[3],
                        "birthdate": user[4],
                        "loginToken": login_token
                    }

                    return jsonify(resp), 200

            elif request.method == 'PATCH':

                data = request.json
                token = data.get("loginToken")
                email = data.get("email")
                username = data.get("username")
                bio = data.get("bio")
                birthdate = data.get("birthdate")
                
                if token != None:

                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        currentUserId = cursor.fetchone()[0]

                        if "email" in data:
                            # check email exists 
                            cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE email=?)", [email])
                            check_email_exists = cursor.fetchone()[0]

                            if check_email_exists == 1:
                                return jsonify({
                                    'message': "Email already exists"
                                }), 400

                            # runs update 
                            cursor.execute("UPDATE user SET email=? WHERE id=?", [email, currentUserId])
                            conn.commit()

                        elif "username" in data:
                            # check username exists 
                            cursor.execute("SELECT EXISTS(SELECT username FROM user WHERE username=?)", [username])
                            check_username_exists = cursor.fetchone()[0]

                            if check_username_exists == 1:
                                return jsonify({
                                    'message': "username already exists"
                                }), 400
                            cursor.execute("UPDATE user SET username=? WHERE id=?",[username, currentUserId])
                            conn.commit()

                        elif "bio" in data:
                            cursor.execute("UPDATE user SET bio=? WHERE id=?",[bio, currentUserId])
                            conn.commit()
                        elif "birthdate" in data:
                            cursor.execute("UPDATE user SET birthdate=? WHERE id=?",[birthdate, currentUserId])
                            conn.commit()
                    

                        cursor.execute("SELECT id, email, username, bio, birthdate FROM user WHERE id=?", [currentUserId])
                        updated = cursor.fetchall()
                        json_data = []
                        row_headers = [x[0] for x in cursor.description]

                        for result in updated:
                            json_data.append(dict(zip(row_headers, result)))
                        return jsonify(json_data[0]), 200
                    else:
                        return jsonify({
                            'message': 'invalid token'
                        }), 400

                else:
                    return jsonify({
                        "message": 'token required'
                    }), 400
            elif request.method == 'DELETE':
                data = request.json
                token = data.get("loginToken")
                password = data.get("password")

                if "password" != data:
                    token
                    password
                    return jsonify({
                        'message': 'Password is required'
                    }),400
                if token != None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT EXISTS(SELECT password FROM user WHERE password=?)", [password])
                        password_valid = cursor.fetchone()[0]
                        if password_valid == 1:

                            cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])
                            userId = cursor.fetchone()[0]

                            cursor.execute("DELETE FROM user_session WHERE login_token=?", [token])
                            conn.commit()
                            cursor.execute("DELETE FROM user WHERE id=?", [userId])
                            conn.commit()

                            cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")
                            return jsonify({

                            }), 200
                        else:
                            return jsonify({
                                'message': 'password is not valid'
                            }),400
                    else:
                        return jsonify({
                            'message': 'Token is not valid'
                        }),400
                else:
                    return jsonify({
                        
                        'message': 'Token is required'
                    }),400
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


def use_data(data):

    user = {
        "userId": data[0],
        "email": data[1],
        "username": data[2],
        "bio": data[3],
        "birthdate": data[4],
    }
    return user
