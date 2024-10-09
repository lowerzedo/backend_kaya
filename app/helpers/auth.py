# # boilerplate jwt auth code for future use
# from functools import wraps
# from flask import request, jsonify
# import jwt


# # auth decorator
# def auth_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         # check if token is in headers
#         if "x-access-token" in request.headers:
#             token = request.headers["x-access-token"]
#         # if no token
#         if not token:
#             return jsonify({"message": "Token is missing!"}), 401
#         try:
#             # decode token
#             data = jwt.decode(token, app.config["SECRET_KEY"])
#             current_user = User.query.filter_by(public_id=data["public_id"]).first()
#         except:
#             return jsonify({"message": "Token is invalid!"}), 401
#         return f(current_user, *args, **kwargs)

#     return decorated
