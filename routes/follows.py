import secrets

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/follows', methods=['GET', 'POST', 'DELETE'])
def followAction():
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
                    userID = data['userId']

                    # checks if integer
                    if not str(userID).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)
                    cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [userID])
                    checkUser = cursor.fetchone()[0]

                
                    if checkUser == 1:
                        cursor.execute("SELECT id as userId, email, username, bio, birthdate FROM user INNER JOIN follow ON user.id = follow.followed WHERE follow.follower=?", [userID])

                        # this will extract row headers
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        json_data = []
                        for result in rv:
                            json_data.append(dict(zip(row_headers, result)))

                        return jsonify(json_data)
                    else:
                        return jsonify({

                            "message": "user not found"
                        }), 400
                else:
                    return jsonify({
                    
                        "message": "userId not found"
                    }), 400

            elif request.method == 'POST':
                data = request.json
                if len(data.keys()) == 2:
                    if {"loginToken", "followId"} <= data.keys():
                        loginToken = data.get("loginToken")
                        followId = data.get("followId")

                        # checks if integer
                        if not str(followId).isdigit():
                            return Response("Not a valid id number", mimetype="text/plain", status=400)

                        if loginToken != None:
                            cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [loginToken])
                            checkToken = cursor.fetchone()[0]

                            if checkToken == 1:
                                cursor.execute("SELECT EXISTS(SELECT id from user WHERE id=?)", [followId])
                                check_follow_id = cursor.fetchone()[0]

                                if check_follow_id == 1:
                                    cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [loginToken])
                                    user_id = cursor.fetchone()[0]

                                    if user_id == int(followId):
                                        return jsonify({
                                            "message": "User cannot follow themselves"
                                        }), 400

                                    cursor.execute("SELECT EXISTS(SELECT followed FROM follow WHERE followed=? AND follower=?)", [followId, user_id])
                                    check_follow_exists = cursor.fetchone()[0]

                                    if check_follow_exists == 0:
                                        cursor.execute("INSERT INTO follow(follower, followed) VALUES(?,?)", [user_id, followId])
                                        conn.commit()
                                        return jsonify({
                                            "message": "You have followed this user"
                                        }), 200

                                    else:
                                        return jsonify({
                                            "message": "This user is already being followed"
                                        }), 400
                                else:
                                    return jsonify({
                                        "message": "No user with that id"
                                    }), 400

                            else:
                                return jsonify({
                                    "message": "Invalid login token"
                                }), 400
                        else:
                            return jsonify({
                                "message": "Invalid login token"
                            }), 400
                    else:
                        return jsonify({
                            'message': "invalid request parameter"
                        }),400

            elif request.method == 'DELETE':
                data = request.json
                if len(data.keys()) == 2:
                    if {"loginToken", "followId"} <= data.keys():
                        loginToken = data.get("loginToken")
                        followId = data.get("followId")

                        # checks if integer
                        if not str(followId).isdigit():
                            return Response("Not a valid id number", mimetype="text/plain", status=400)

                        if loginToken is not None:
                            cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [loginToken])
                            checkToken = cursor.fetchone()[0]

                            if checkToken == 1:
                                cursor.execute("SELECT EXISTS(SELECT id from user WHERE id=?)", [followId])
                                check_follow_id = cursor.fetchone()[0]

                                if check_follow_id == 1:
                                    cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [loginToken])
                                    user_id = cursor.fetchone()[0]

                                    if user_id == int(followId):
                                        return jsonify({
                                            "message": "User cannot unfollow themselves"
                                        }), 400

                                    cursor.execute("SELECT EXISTS(SELECT followed FROM follow WHERE followed=? AND follower=?)", [followId, user_id])
                                    check_follow_exists = cursor.fetchone()[0]

                                    if check_follow_exists == 1:
                                        cursor.execute("DELETE FROM follow WHERE follower=? AND followed=?", [user_id, followId])
                                        conn.commit()
                                        return jsonify({
                                            "message": "You have unfollow this user"
                                        }), 200

                                    else:
                                        return jsonify({
                                            "message": "This user is not followed"
                                        }), 400
                                else:
                                    return jsonify({
                                        "message": "No user with that id"
                                    }), 400

                            else:
                                return jsonify({
                                    "message": "Invalid login token"
                                }), 400
                        else:
                            return jsonify({
                                "message": "Invalid login token"
                            }), 400
                    else:
                        return jsonify({
                            'message': "invalid request"
                        }),400
            else:
                return jsonify({
                    'message': "invalid request"
                }), 500
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