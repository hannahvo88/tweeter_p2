

import mariadb
from flask import Response, request, jsonify
import secrets
import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/login', methods=['POST', 'DELETE'])
def login_handler():
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
            if request.method == 'POST':
                data = request.json
                if len(data.keys()) == 2:
                    if {"email", "password"} <= data.keys():
                        email = data.get("email")
                        password = data.get("password")

                        cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE email=?)", [email])
                        email_valid = cursor.fetchone()[0]

                        if email_valid == 1:
                            cursor.execute("SELECT id AS userId, email, username, bio, birthdate FROM user ""WHERE email=? AND password=?", [email, password])
                            # this will extract row headers
                            row_headers = [x[0] for x in cursor.description]
                            rv = cursor.fetchall()
                            if len(rv) > 0:
                                json_data = []
                                for result in rv:
                                    json_data.append(dict(zip(row_headers, result)))

                                res = json_data[0]

                                login_token = secrets.token_hex(16)

                                res['loginToken'] = login_token
                                user_Id = res['userId']
                                cursor.execute("INSERT INTO user_session(user_id, login_token) VALUES(?,?)",[user_Id, login_token])
                                conn.commit()

                                return jsonify(res), 200
                            else:
                                return jsonify({
                                    'message': "email not found"
                                }),400
                        else:
                            return jsonify({

                                'message': "email/username not found"
                            }),400

                    elif {"username", "password"} <= data.keys():
                        username = data.get("username")
                        password = data.get("password")
                        cursor.execute("SELECT EXISTS(SELECT email FROM user WHERE username=?)", [username])
                        username_valid = cursor.fetchone()[0]

                        if username_valid == 1:
                            cursor.execute("SELECT id AS userId, email, username, bio, birthdate FROM user ""WHERE username=? AND password=?", [username, password])
                            
                            # this will extract row headers
                            row_headers = [x[0] for x in cursor.description]
                            rv = cursor.fetchall()
                            if len(rv) > 0:
                                json_data = []
                                for result in rv:
                                    json_data.append(dict(zip(row_headers, result)))

                                res = json_data[0]

                                login_token = secrets.token_hex(16)

                                res['loginToken'] = login_token
                                user_Id = res['userId']

                                cursor.execute("INSERT INTO user_session(user_id, login_token) VALUES(?,?)",[user_Id, login_token])
                                conn.commit()

                                return jsonify(res), 200
                            else:
                                return jsonify({
                                    'message': "username not found"
                                }),400
                        else:
                            return jsonify({

                                'message': "username not found"
                            }),400
                    else:
                        if "username" != data and "email" != data:
                            return jsonify({

                                'message': "email/username required"
                            }),400
                        elif "password" != data:
                            return jsonify({
                                
                                'message': "Password required"
                            }),400
                else:
                    return jsonify({
                        'message': "Request data invalid"
                    }),400

            elif request.method == "DELETE":
                data = request.json
                loginToken = data.get("loginToken")
                if "loginToken" in data:
                    cursor.execute("SELECT EXISTS(SELECT id FROM user_session WHERE login_token=?)", [loginToken])
                    token_valid = cursor.fetchone()[0]
                    
                    if token_valid == 1:
                        cursor.execute("DELETE FROM user_session WHERE login_token=?", [loginToken])
                        conn.commit()
                        return jsonify({}), 200
            else:
                return jsonify({
                    "message": request.method + " Method not support"
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
