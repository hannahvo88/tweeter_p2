
from datetime import datetime

import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/tweets', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def tweets_handler():
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
            if request.method == "GET":
                data = request.json
                if data != None and "userId" in data:
                    userID = data.get("userId")

                    # checks if integer
                    if not str(userID).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    cursor.execute("SELECT EXISTS(SELECT * FROM user WHERE id=?)", [userID])
                    checkUser = cursor.fetchone()[0]

                    if checkUser == 1:
                        cursor.execute("SELECT tweet.id, user_id, username, content, created_at FROM tweet INNER JOIN user ON tweet.user_id = user.id where tweet.user_id=?",[userID])
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        json_data = []
                        for result in rv:
                            json_data.append(dict(zip(row_headers, result)))
                        return jsonify(json_data), 200
                    else:
                        return jsonify({
                            'message': "User not found"
                        }), 404
                else:
                    cursor.execute("SELECT tweet.id, user_id, username, content, created_at FROM tweet INNER JOIN user ON tweet.user_id = user.id")
                    row_headers = [x[0] for x in cursor.description]
                    rv = cursor.fetchall()
                    json_data = []
                    for result in rv:
                        json_data.append(dict(zip(row_headers, result)))
                    return jsonify(json_data), 200

            elif request.method == "POST":
                data = request.json

                if len(data.keys()) == 2:
                    if {"loginToken", "content"} <= data.keys():
                        data
                    else:
                        return jsonify({
                            'message': "Incorrect keys submitted.",
                        }), 400

                else:
                    return jsonify({
                        'message': "Incorrect keys submitted.",
                    }), 400

                token = data.get("loginToken")
                tweet_content = data.get("content")
                if token != None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    checkToken = cursor.fetchone()[0]

                    if checkToken == 0:
                        return jsonify({
                            'message': "Not a valid login token",
                        }), 400
                else:
                    return jsonify({
                        'message': "Invalid login token",
                    }), 400

                created_date = datetime.now()
                
                cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])
                user_id = cursor.fetchone()[0]
                

                cursor.execute("INSERT INTO tweet(user_id, content, created_at) VALUES(?,?,?)", [user_id, tweet_content, created_date])
                conn.commit()
                
                cursor.execute("SELECT tweet.id, user.id, username, content, created_at FROM tweet INNER JOIN user ON tweet.user_id = user.id WHERE tweet.user_id=? ORDER BY tweet.id DESC LIMIT 1", [user_id])
                ret_data = cursor.fetchone()
                resp = {
                    "tweetId": ret_data[0],
                    "userId": ret_data[1],
                    "username": ret_data[2],
                    "content": ret_data[3],
                    "createdAt": ret_data[4],
                    
                }
                return jsonify(resp), 200


            elif request.method == "PATCH":
                data = request.json
                
                if len(data.keys()) == 3:
                    if {"loginToken", "tweetId", "content"} <= data.keys():

                        token = data.get("loginToken")
                        tweet_id = data.get("tweetId")
                        content = data.get("content")
                        # checks if integer
                        if not str(tweet_id).isdigit():
                            return Response("Not a valid id number", mimetype="text/plain", status=400)

                        if token != None:
                            cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                            token_valid = cursor.fetchone()[0]

                            if token_valid == 1:
                                cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [tweet_id])
                                tweetvalid = cursor.fetchone()[0]

                                if tweetvalid == 1:
                                    cursor.execute("SELECT EXISTS (SELECT tweet.id FROM user_session INNER JOIN tweet ON user_session.user_id = tweet.user_id WHERE login_token=? AND tweet.id=?)",[token, tweet_id])
                                    user_valid = cursor.fetchone()[0]

                                    if user_valid == 0:
                                        return jsonify({
                                            "message": "Unauthorized to update this tweet"
                                        }), 400
                                    
                                    cursor.execute("UPDATE tweet SET content=? WHERE id=?", [content, tweet_id])
                                    conn.commit()

                                    cursor.execute("SELECT id, content FROM tweet WHERE id=?", [tweet_id])
                                    new_tweet = cursor.fetchone()

                                    resp = {
                                        "tweetId": new_tweet[0],
                                        "content": new_tweet[1],
                                    }
                                    return jsonify(resp), 200
                                else:
                                    return jsonify({
                                        'message': "Invalid tweet id"
                                    }), 400
                            else:
                                return jsonify({
                                    'message': "Invalid login token"
                                }), 400
                        return jsonify({
                            "message": request.method + " Method not support"
                        }),400
                    else:
                        return jsonify({
                            'message': "Invalid Request Key"
                        }), 400
                else:
                    return jsonify({
                        'message': "Invalid Request"
                    }), 400

            elif request.method == "DELETE":
                data = request.json

            if len(data.keys()) == 2 and {"loginToken", "tweetId"} <= data.keys():
                tweet_id = data.get("tweetId")
                token = data.get("loginToken")
                # checks if valid positive integer
                if not str(tweet_id).isdigit():
                    return Response("Not a valid id number", mimetype="text/plain", status=400)
                if token is not None:
                    cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                    token_valid = cursor.fetchone()[0]

                    if token_valid == 1:
                        cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [tweet_id])
                        checkTweet = cursor.fetchone()[0]

                        if checkTweet == 1:
                            cursor.execute("SELECT EXISTS (SELECT tweet.id FROM user_session INNER JOIN tweet ON user_session.user_id = tweet.user_id WHERE login_token=? AND tweet.id=?)", [token, tweet_id])
                            userHasTweet = cursor.fetchone()[0]

                            if userHasTweet == 1:
                                cursor.execute("DELETE FROM tweet WHERE id=?", [tweet_id])
                                conn.commit()
                                return jsonify({
                                    "message": "you have deleted this tweet"
                                }), 200

                            else:
                                return jsonify({
                                    "message": "you are not permitted to delete this tweet"
                                }), 400
                        else:
                            return jsonify({
                                "message": "Invalid tweet id"
                            }), 400
                    else:
                        return jsonify({
                            "message": "Invalid login token"
                        }), 400
                else:
                    return jsonify({
                        "message": "login token required"
                    }), 400
            else:
                return jsonify({
                    "message": "invalid request"
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
      