from flask import Flask, request, jsonify, abort
from flask.logging import default_handler
from werkzeug.contrib.fixers import ProxyFix
from datetime import datetime
import logging
from logging.config import dictConfig
import os
from secrets import SECRET_KEY_FLASK
import hashlib
import hmac
import werkzeug.security
import subprocess
from yaml import load, dump
try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.FileHandler',
    #        'stream': 'ext://flask.logging.wsgi_errors_stream',
            'filename' : 'app.log',
            'formatter': 'default'
        }},
        'root': {
            'level': 'DEBUG',
            'handlers': ['wsgi']
        }
})

def check_signature(signature, key, data):
    """Compute the HMAC signature and test against a given hash."""
    if isinstance(key, type(u'')):
        key = key.encode()
        
    digest = 'sha1=' + hmac.new(key, data, hashlib.sha1).hexdigest()
    
    # Covert everything to byte sequences
    if isinstance(digest, type(u'')):
        digest = digest.encode()
    if isinstance(signature, type(u'')):
        signature = signature.encode()
    
    return werkzeug.security.safe_str_cmp(digest, signature)

app = Flask(__name__)
app.secret_key = SECRET_KEY_FLASK
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/')
def index():
        return "Welcome, you should know where to go ;)"

@app.route('/hooks/<t>/<repo>/', methods=['POST'])
def hook(t, repo):
    with open('config.yaml', 'r') as stream:
        config = load(stream, Loader=Loader)

    if repo not in config:
        log.info("repo {} not in config".format(repo))
        return "repo not in config!", 404

    key = config[repo]["key"]

    if t == "github":
        signature = request.headers.get('X-Hub-Signature')
        if not signature:
            app.logger.info("repo {} missing signature".format(repo))
            return "missing signature", 400

        payload = request.get_data()

        if not check_signature(signature, key, payload):
            app.logger.info("repo {} invalid signature".format(repo))
            return "invalid signature", 403

        event = request.headers.get('X-Github-Event')

        if not event:
            app.logger.info("repo {} missing github event header".format(repo))
            return "missing github event", 400
    else:
        app.logger.info("repo {}  unkown type: {}".format(repo, t))
        return "unkown type {}".format(t), 400

    if event == "ping":
        app.logger.info("repo {} pinged".format(repo))
        return "PONG", 200

    if event != config[repo]["event"]:
        app.logger.info("repo {} event {} no action".format(repo, event))
        return "not a {} event, do nothing".format(event), 200

    payload = request.get_json()
    if payload['ref'] != "refs/heads/" + config[repo]["branch"]:
        app.logger.info("repo {} event for other ref {}".format(repo, payload['ref']))
        return "not for branch {}".format(config[repo]["branch"]), 200
    
    cwd = config[repo]["cwd"]

    results = ""
    for action in config[repo]["actions"]:
        try:
            grepOut = subprocess.check_output(action.split(' '), cwd=cwd)
        except subprocess.CalledProcessError as grepexc:
            error = "action '{}' error code {} output: {}".format(action, grepexc.returncode, grepexc.output)
            app.logger.info("repo: {} => ".format(repo) + error)
            return error, 400
        results += grepOut.decode() + "\n"

    app.logger.info("actions for repo {} done".format(repo))
    return results, 200
