from flask import Flask, request
from flask_sockets import Sockets
from requests import get
import requests_cache


app = Flask(__name__)
sockets = Sockets(app)
SITE_NAME = ''
requests_cache.install_cache('cache', backend='sqlite', expire_after=180)

@sockets.route('/echo')
def echo_socket(ws):
    while not ws.closed:
        message = ws.receive()
        ws.send(message)

@app.route('/') 
def hello(): 
    return 'Hello World!'

# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def proxy(path):
#     url = request.args.get('url', default='google.com', type = str)
#     SITE_NAME = "https://" + url + "/"
#     response = get(SITE_NAME)
#     print("Used Cache: {}".format(response.from_cache))
#     return get(f'{SITE_NAME}{path}').content   

if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
 
    server = pywsgi.WSGIServer(('', 5200), app, handler_class=WebSocketHandler)
    server.serve_forever()