from datetime import datetime
import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/comments', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def comment_handler():
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
                tweetId = data.get("tweetId")

                if "tweetId" in data:
                    tweetId

                    # checks if integer
                    if not str(tweetId).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    cursor.execute("SELECT EXISTS(SELECT id from tweet WHERE id=?)", [tweetId])
                    checkTweet = cursor.fetchone()[0]

                    if checkTweet == 1:
                        cursor.execute("SELECT comment.id, comment.created_at, comment.tweet_id, comment.content, user.username, user.id FROM comment INNER JOIN user ON comment.user_id = user.id WHERE comment.tweet_id=?", [tweetId])
                        
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        json_data = []
                        for result in rv:
                            json_data.append(dict(zip(row_headers, result)))

                        return jsonify(json_data), 200
                    else:
                        return jsonify({
                            "message": "Tweet can not been found"
                        }), 400
                else:
                    return jsonify({
                        "message": "Invalid requests"
                    }), 400

            elif request.method == "POST":
                data = request.json
                tweet_id = data.get("tweetId")
                content = data.get("content")
                if len(data.keys()) == 3 and {"loginToken", "tweetId", "content"} <= data.keys():
                    tweet_id

                    # checks if integer
                    if not str(tweet_id).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    token = data.get("loginToken")

                    if token != None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                            userId = cursor.fetchone()[0]

                            cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [tweet_id])
                            check_tweet = cursor.fetchone()[0]

                            if check_tweet == 1:

                                created_date = datetime.now()
                                cursor.execute("INSERT INTO comment(user_id, tweet_id, content, created_at) VALUES(?,?,?,?)", [userId, tweet_id, content, created_date])
                                conn.commit()
                                lastId = cursor.lastrowid

                                cursor.execute("SELECT comment.id, comment.created_at, comment.tweet_id, comment.content, user.username, user.id FROM comment INNER JOIN user ON comment.user_id = user.id WHERE comment.id=?", [lastId])
                                row_headers = [x[0] for x in cursor.description]
                                rv = cursor.fetchall()
                                json_data = []
                                for result in rv:
                                    json_data.append(dict(zip(row_headers, result)))

                                return jsonify(json_data), 200

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
            elif request.method == "PATCH":
                data = request.json
                commentId = data.get("commentId")
                content = data.get("content")
                if len(data.keys()) == 3 and {"loginToken", "commentId", "content"} <= data.keys():
                    commentId 

                    # checks if integer
                    if not str(commentId).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    token = data.get("loginToken")

                    if token != None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                            userId = cursor.fetchone()[0]

                            cursor.execute("SELECT EXISTS(SELECT id FROM comment WHERE id=? AND user_id=?)", [commentId, userId])
                            check_comment = cursor.fetchone()[0]

                            if check_comment == 1:
                                cursor.execute("UPDATE comment SET content=? where id=?", [content, commentId])
                                conn.commit()

                                cursor.execute("SELECT comment.id, comment.created_at, comment.tweet_id, comment.content,user.username, user.id FROM comment INNER JOIN user ON comment.user_id = user.id WHERE comment.id=?", [commentId])
                                row_headers = [x[0] for x in cursor.description]
                                rv = cursor.fetchall()
                                json_data = []
                                for result in rv:
                                    json_data.append(dict(zip(row_headers, result)))

                                return jsonify(json_data), 200

                            else:
                                return jsonify({
                                    "message": "comment not found"
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
                commentId = data.get("commentId")
                if len(data.keys()) == 2 and {"loginToken", "commentId"} <= data.keys():
                    commentId 

                    # checks if integer
                    if not str(commentId).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    token = data.get("loginToken")

                    if token != None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                            userId = cursor.fetchone()[0]

                            cursor.execute("SELECT EXISTS(SELECT id FROM comment WHERE id=? and user_id=?)", [commentId, userId])
                            checkComment = cursor.fetchone()[0]

                            if checkComment == 1:
                                cursor.execute("DELETE FROM comment WHERE user_id=? AND id=?", [userId, commentId])

                                conn.commit()
                                return jsonify({
                                    "message": "You have successfully deleted your comment"
                                }), 200

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