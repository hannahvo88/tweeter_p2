
import mariadb
from flask import Response, request, jsonify
import json
import secrets
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
                rq = request.args
                print(rq)
                if len(rq.keys()) == 0:
                    cursor.execute("SELECT *FROM user")

                    # this will extract row headers
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))

                    res = json_data
                elif len(rq.keys()) == 1:
                    print('here')
                    if rq.get('userId').isdigit():
                        cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [rq.get('userId')])
                        check_id_valid = cursor.fetchone()[0]
                        if check_id_valid == 1:
                            cursor.execute(f"SELECT * FROM user WHERE id='{rq.get('userId')}'")

                            # this will extract row headers
                            row_headers = [x[0] for x in cursor.description]
                            rv = cursor.fetchall()
                            json_data = []
                            for result in rv:
                                json_data.append(dict(zip(row_headers, result)))

                            res = json_data
                        else:
                            return jsonify({
                                'status': 400,
                                'message': "User id does not found"
                            })
                    else:
                        return jsonify({
                            'status': 400,
                            'message': "Invalid Request"
                        })
                else:
                    return jsonify({
                        'status': 400,
                        'message': "Invalid Request"
                    })

                return jsonify(res), 200
            elif request.method == 'POST':
                data = request.json

                print(data)

                validated = required_params({
                    "email": "",
                    "username": "",
                    "birthdate": "",
                    "bio": "",
                    "password": ""
                })

                if not validated['status']:
                    return jsonify({
                        "status": 400,
                        "message": "Request JSON is missing some required params",
                        "missing": validated['data']
                    })
                else:

                    # check email exists 
                    cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE email=?)", [data["email"]])
                    check_email_exists = cursor.fetchone()[0]

                    if check_email_exists == 1:
                        return jsonify({
                            'status': 400,
                            'message': "Email already exists"
                        })

                    # check username exists 
                    cursor.execute("SELECT EXISTS(SELECT username FROM user WHERE username=?)", [data["username"]])
                    check_username_exists = cursor.fetchone()[0]

                    if check_username_exists == 1:
                        return jsonify({
                            'status': 400,
                            'message': "Username already exists"
                        })

                    # insert data
                    cursor.execute("INSERT INTO user(email, username, password, bio, birthdate) VALUES(?,?,?,?,?)", [data["email"], data["username"],data["password"], data["bio"],data["birthdate"]])
                    conn.commit()
                    cursor.execute("SELECT id FROM user WHERE email=?", [data["email"]])
                    user_id = cursor.fetchone()[0]

                    login_token = secrets.token_hex(16)
                    cursor.execute("INSERT INTO user_session(user_id, login_token) VALUES(?,?)", [user_id, login_token])
                    conn.commit()

                    cursor.execute("SELECT id, email, username, bio, birthdate FROM user WHERE id=?",[user_id])
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
                if token != None:

                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                        currentUserId = cursor.fetchone()[0]
                        print("current user ", currentUserId)

                        if "email" in data:
                            # check email exists 
                            cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE email=?)", [data["email"]])
                            email_exists = cursor.fetchone()[0]

                            if email_exists == 1:
                                return jsonify({
                                    'status': 400,
                                    'message': "Email already exists"
                                })

                            # runs update if all email checks pass
                            cursor.execute("UPDATE user  SET email=? WHERE id=?", [data["email"], currentUserId])
                            conn.commit()

                        elif "username" in data:

                            # check ALL INFORMATION IF exists
                            cursor.execute("SELECT EXISTS(SELECT username FROM user WHERE username=?)", [data["username"]])
                            username_exists = cursor.fetchone()[0]

                            if username_exists == 1:
                                return jsonify({
                                    'status': 400,
                                    'message': "username already exists"
                                })
                            cursor.execute("UPDATE user  SET username=? WHERE id=?",[data["username"], currentUserId])
                            conn.commit()

                        elif "bio" in data:
                            cursor.execute("UPDATE user  SET bio=? WHERE id=?",[data["bio"], currentUserId])
                            conn.commit()
                        elif "birthdate" in data:
                            cursor.execute("UPDATE user  SET birthdate=? WHERE id=?",[data["birthdate"], currentUserId])
                            conn.commit()

                        cursor.execute(
                            "SELECT id as userId, email, username, bio, birthdate FROM user  WHERE id=?",[currentUserId])
                        updated_user = cursor.fetchall()
                        json_data = []
                        row_headers = [x[0] for x in cursor.description]

                        for result in updated_user :
                            json_data.append(dict(zip(row_headers, result)))
                        return jsonify(json_data[0]), 200
                    else:
                        return jsonify({
                            'status': 400,
                            'message': 'invalid token'
                        })

                else:
                    return jsonify({
                        'status': 400,
                        'message': 'token required'
                    })
            elif request.method == 'DELETE':
                data = request.json
                token = data.get("loginToken")

                if "password" not in data:
                    return jsonify({
                        'status': 400,
                        'message': 'Password is required'
                    })
                if token != None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT EXISTS(SELECT password FROM user WHERE password=?)", [data['password']])
                        password_valid = cursor.fetchone()[0]
                        if password_valid == 1:

                            print(token)
                            cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])
                            userId = cursor.fetchone()[0]

                            print(userId)

                            cursor.execute("DELETE FROM user_session WHERE login_token=?", [token])
                            conn.commit()
                            cursor.execute("DELETE FROM user WHERE id=?", [userId])
                            conn.commit()

                            cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")
                            return jsonify({}), 200
                        else:
                            return jsonify({
                                'status': 400,
                                'message': 'password is not valid'
                            })
                    else:
                        return jsonify({
                            'status': 400,
                            'message': 'Token is not valid'
                        })
                else:
                    return jsonify({
                        'status': 400,
                        'message': 'Token is required'
                    })
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
    print(data)
    user = {
        "userId": data[0],
        "email": data[1],
        "username": data[2],
        "bio": data[3],
        "birthdate": data[4],
    }
    return user


