import socket
import sys
import signal
import threading
import select


def close_proxy(signal, frame):
    print("Interruption.")
    sys.exit(0)

# Where the blocked sites are stored:
blacklist = ["tcd.blackboard.com"]
signal.signal(signal.SIGINT, close_proxy)
current_conns = 0  # currently established connections

config = {
    "HOST": "localhost",
    "PORT": 4008,
    "MAX_CONNS": 40,
    "BUFFER_SIZE": 4092,  # max current_conns of bytes that can be received at once for http
}


# Function: Initialise program
# Description: Creates sockets and binds and listens to the server
#              Listens to the clients, accepting the connection and creating a new socket object
#              Generates multi-threads for the connections and keeps of track of how many threads are active

def main():
    global current_conns

    print("Proxy server running on port: " + str(config['PORT']))

    try:
        # create a TCP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((config['HOST'], config['PORT']))

        # socket.listen() has a backlog parameter which specifies how many connections
        # it will allow before refusing new ones.
        s.listen(config['MAX_CONNS'])

    except socket.error:
        print("Socket error, run again to retry")
        sys.exit(1)

    # set up client listeners
    while current_conns <= config['MAX_CONNS']:
        # Check blacklist file for newly added blocked urls, dynamic blocking
        with open('blacklist.txt') as f:
            for entry in f:
                 if entry not in blacklist and entry != '\n':
                    entry.rstrip()
                    blacklist.append(entry)
        
        if (current_conns < config['MAX_CONNS']):
            current_conns += 1
            # accept incoming connection
            # create new socket object seperate from our currently listening socket above
            conn, addr = s.accept()
            # Create a new thread for new client
            thread = threading.Thread(name=addr, target=proxyServer, args=(conn, addr))
            thread.setDaemon(True)
            thread.start()
            print("Active threads: ", threading.active_count())


# Function: Handle requests to and from browser
# Description: Deals with HTTP and HTTPS requests
#              Checks for blocked URLS
def proxyServer(conn, addr):
    global current_conns
    data = conn.recv(config["BUFFER_SIZE"])  # get protocol of request from browser
    url_blocked = False
    empty = b''

# Code below was adapted from geeksforgeeks.org to support:
#                                                             -> HTTP + HTTPS
#                                                             -> Dynamic blocking of URL's
#                                                             -> Caching
    if data is not empty:
        try:
            parse_line = data.decode().split('\n')[0]  # parse the first line

            try:
                url = parse_line.split(' ')[1]  # get URL
                protocol = ""

                if "CONNECT" in parse_line: # The CONNECT keyword passed by the browser indicates HTTPS
                    protocol = "https"

                else:
                    protocol = "http"

                # Check if URL is blacklisted
                for i in range(0, len(blacklist)):  # check if site is already blocked
                    if blacklist[i] in url:
                        print("Blocked URL site: " + url + "\n")
                        url_blocked = True
                        conn.close()

                if url_blocked is False:
                    print("Request: ", parse_line, addr)

                    # copy of url
                    http_pos = url.find("://")

                    if (http_pos == -1):
                        temp = url

                    elif (protocol == "http"):
                        temp = url[(http_pos + 3):]

                    else:
                        temp = url[(http_pos + 4):]

                    # find webserver
                    port_pos = temp.find(":") # port pos (if any)

                    webserver_pos = temp.find("/")
                    if webserver_pos == -1:
                        webserver_pos = len(temp)

                    webserver = ""
                    port = -1

                    if (port_pos == -1 or webserver_pos < port_pos):
                        if (protocol == "https"):
                            port = 443
                        else:
                            port = 80
                        webserver = temp[:webserver_pos]
                    else:
                        port = int((temp[(port_pos + 1):])
                                   [:webserver_pos - port_pos - 1])
                        webserver = temp[:port_pos]

                    print("Connect to: ", webserver, port,  "\n")

                    # create new socket to connect to the web server
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((webserver, port))

                    if protocol == "http":
                        s.send(data)  # send request to web server

                        while True:
                            try:
                                server_data = s.recv(config["BUFFER_SIZE"])

                            except socket.error:
                                print("Connection timeout")
                                s.close()
                                conn.close()
                                current_conns = current_conns - 1

                            if (len(server_data) > 0):
                                conn.send(server_data)  # send to browser

                            else:
                                conn.close()
                                s.close()
                                current_conns = current_conns - 1

                    if protocol == "https":
                        # send response to the browser
                        conn.send(bytes("HTTP/1.1 200 Connection Established\r\n\r\n", "utf8"))

                        # store both sockets: browser and server
                        connections = [conn, s]
                        keep_alive = True

                        while keep_alive:
                            keep_alive = False
                            ready_sockets, sockets_for_writing, error_sockets = select.select(connections, [], connections, 100)

                            if error_sockets:
                                break

                            for r_socket in ready_sockets:
                                # look for a ready socket
                                other = connections[1] if r_socket is connections[0] else connections[0]

                                try:
                                    # buffer size for HTTPS
                                    data = r_socket.recv(8192)

                                except socket.error:                   
                                    print("Connection timeout")
                                    r_socket.close()

                                if data:
                                    other.sendall(data)
                                    keep_alive = True
                    else:
                        pass
            except IndexError:
                pass
        except UnicodeDecodeError:
            pass
    else:
        pass

    current_conns = current_conns - 1
    conn.close()         




if __name__ == '__main__':
    main()
