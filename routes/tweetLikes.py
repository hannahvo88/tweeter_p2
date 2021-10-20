from datetime import datetime
import json
import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/tweet-likes', methods=['GET', 'POST', 'DELETE'])
def tweetLikesAction():
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

                if "tweetId" in data:
                    tweetId = data.get("tweetId")

                    # checks if integer
                    if not str(tweetId).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [tweetId])
                    check_tweet = cursor.fetchone()[0]

                    if check_tweet == 1:
                        cursor.execute("SELECT tweet_like.tweet_id, user.id, user.username FROM tweet_like INNER JOIN user ON tweet_like.user_id = user.id WHERE tweet_like.tweet_id=?", [tweetId])
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        json_data = []

                        for result in rv:
                            json_data.append(dict(zip(row_headers, result)))

                        return jsonify(json_data), 200
                    else:
                        return jsonify({
                            "message": "Can not find this post"
                        }), 400
                else:
                    return jsonify({
                        "message": "Invalid requests"
                    }), 400

            elif request.method == "POST":
                data = request.json

                if len(data.keys()) == 2 and {"loginToken", "tweetId"} <= data.keys():
                    tweet_id = data.get("tweetId")
                    token = data.get("loginToken")

                    # checks if integer
                    if not str(tweet_id).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    if token != None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                            userId = cursor.fetchone()[0]

                            cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [tweet_id])
                            checkTweet = cursor.fetchone()[0]

                            if checkTweet == 1:

                                cursor.execute("SELECT EXISTS(SELECT id FROM tweet_like WHERE tweet_id=? AND user_id=?)", [tweet_id, userId])
                                tweet_liked = cursor.fetchone()[0]

                                if tweet_liked == 0:
                                    created_date = datetime.now()
                                    cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")

                                    cursor.execute("INSERT INTO tweet_like(user_id,tweet_id, created_at) VALUES(?,?,?)",[userId, tweet_id, created_date])

                                    cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")
                                    conn.commit()

                                    return jsonify({
                                        "message": "you liked this tweet"
                                    }), 200
                                else:
                                    return jsonify({
                                        "message": "you already liked this tweet"
                                    }), 400
                            else:
                                return jsonify({
                                    "message": "tweet not found"
                                }), 400
                        else:
                            return jsonify({
                                "message": "token invalid"
                            }), 400
                    else:
                        return jsonify({
                            "message": "loginToken Required"
                        }), 400
                else:
                    return jsonify({
                        "message": "invalid request params"
                    }), 400

            elif request.method == "DELETE":
                data = request.json

                if len(data.keys()) == 2 and {"loginToken", "tweetId"} <= data.keys():
                    tweet_id = data.get("tweetId")
                    token = data.get("loginToken")

                    # checks if integer
                    if not str(tweet_id).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    if token != None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                            userId = cursor.fetchone()[0]

                            cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [tweet_id])
                            check_tweet = cursor.fetchone()[0]

                            if check_tweet == 1:

                                cursor.execute("SELECT EXISTS(SELECT id FROM tweet_like WHERE tweet_id=? AND user_id=?)", [tweet_id, userId])
                                tweet_liked = cursor.fetchone()[0]
                                if tweet_liked == 1:
                                    cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")

                                    cursor.execute("DELETE FROM tweet_like WHERE user_id=? AND tweet_id=?", [userId, tweet_id])

                                    cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")
                                    conn.commit()
                                    return jsonify({
                                        "message": "you have unliked this tweet"
                                    }), 200
                                else:
                                    return jsonify({
                                        "message": "you did not liked this tweet"
                                    }), 400
                            else:
                                return jsonify({
                                    "message": "tweet not found"
                                }), 400
                        else:
                            return jsonify({
                                "message": "token invalid"
                            }), 400
                    else:
                        return jsonify({
                            "message": "loginToken Required"
                        }), 400
                else:
                    return jsonify({
                        "message": "invalid request params"
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

