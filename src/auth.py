import os
from functools import wraps

from dotenv import load_dotenv
from flask import request, jsonify


load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "missing Authorization header"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "invalid Authorization header"}), 401

        token = auth_header.removeprefix("Bearer ")

        if token != API_TOKEN:
            return jsonify({"error": "invalid token"}), 401

        return fn(*args, **kwargs)

    return wrapper