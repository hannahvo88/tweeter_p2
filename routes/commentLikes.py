from datetime import datetime
import mariadb
from flask import request, jsonify, Response

import dbcreds
from apptoken import xApiToken
from routes import app


@app.route('/api/comment-likes', methods=['GET', 'POST', 'DELETE'])
def commentLikes_handler():
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
                commentId = data.get('commentId')

                if len(data.keys()) == 1 and "commentId" in data:
                    commentId

                    # checks if integer
                    if not str(commentId).isdigit():
                        return Response("Not a valid id number", mimetype="text/plain", status=400)

                    cursor.execute("SELECT EXISTS(SELECT id FROM comment WHERE id=?)", [commentId])
                    check_tweet = cursor.fetchone()[0]

                    if check_tweet == 1:
                        cursor.execute(
                            "SELECT comment_like.comment_id, user.id, user.username FROM comment_like INNER JOIN user ON comment_like.user_id = user.id WHERE comment_like.comment_id=?", [commentId])
                        row_headers = [x[0] for x in cursor.description]
                        rv = cursor.fetchall()
                        json_data = []
                        for result in rv:
                            json_data.append(dict(zip(row_headers, result)))

                        return jsonify(json_data), 200
                    else:
                        return jsonify({
                            "message": "Comment not found"
                        }), 400
                else:
                    return jsonify({
                        "message": "Invalid requests"
                    }), 200

            elif request.method == "POST":
                data = request.json
                commentId = data.get("commentId")
                token = data.get("loginToken")

                if len(data.keys()) == 2 and {"loginToken", "commentId"} <= data.keys():
                    commentId 
                    token

                    if token != None:
                        cursor.execute("SELECT EXISTS(SELECT login_token FROM user_session WHERE login_token=?)", [token])
                        token_valid = cursor.fetchone()[0]

                        if token_valid == 1:
                            cursor.execute("SELECT user_id FROM user_session WHERE login_token=?", [token])

                            userId = cursor.fetchone()[0]

                            cursor.execute("SELECT EXISTS(SELECT id FROM comment WHERE id=?)", [commentId])
                            check_comment = cursor.fetchone()[0]

                            if check_comment == 1:

                                cursor.execute("SELECT EXISTS(SELECT id FROM comment_like WHERE comment_id=? AND user_id=?)", [commentId, userId])
                                comment_liked = cursor.fetchone()[0]

                                if comment_liked == 0:

                                    created_date = datetime.now()

                                    cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                                    cursor.execute("INSERT INTO comment_like(user_id,comment_id, created_at) VALUES(?,?,?)", [userId, commentId, created_date])
                                    cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")

                                    conn.commit()
                                    return jsonify({
                                        "message" : "You like this comment!"
                                    }), 200
                                else:
                                    return jsonify({
                                        "message": "You already liked this comment"
                                    }), 400
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

                            cursor.execute("SELECT EXISTS(SELECT id FROM tweet WHERE id=?)", [commentId])
                            check_comment = cursor.fetchone()[0]

                            if check_comment == 1:

                                cursor.execute("SELECT EXISTS(SELECT id FROM comment_like WHERE comment_id=? AND user_id=?)", [commentId, userId])
                                comment_liked = cursor.fetchone()[0]

                                if comment_liked == 1:
                                    cursor.execute("SET FOREIGN_KEY_CHECKS=OFF;")
                                    cursor.execute("DELETE FROM comment_like WHERE user_id=? AND comment_id=?", [userId, commentId])
                                    cursor.execute("SET FOREIGN_KEY_CHECKS=ON;")

                                    conn.commit()
                                    return jsonify({
                                        "message" : "You have unliked this comment!"
                                    }), 200
                                else:
                                    return jsonify({
                                        "message": "You did not liked this comment"
                                    }), 400
                            else:
                                return jsonify({
                                    "message": "Comment not found"
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
