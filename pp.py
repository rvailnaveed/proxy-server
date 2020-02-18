from flask import Flask
from flask_sockets import Sockets
from requests import get


app = Flask(__name__)
sockets = Sockets(app)
SITE_NAME = 'https://youtube.com/'

@sockets.route('/echo')
def echo_socket(ws):
    while not ws.closed:
        message = ws.receive()
        ws.send(message)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # if SITE_NAME == 'https://google.com/':
    #     return "blocked"

   # print(get(f'{SITE_NAME}{path}').content)
    print(SITE_NAME)
    print(path)
    return get(f'{SITE_NAME}{path}').content


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5100), app, handler_class=WebSocketHandler)
    server.serve_forever()