import socket
import imageio
import os


#host ip and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080

#open up socket and listen to port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)

def ReadFile(filename):

    type = filename.split('.')[1]
    if os.path.isfile("htdocs" + filename):
        file = open('htdocs' + filename)
        print("file found: " + type)
        if type == 'html' or type == 'script' or type == 'css' or type == 'txt':
            content = file.read()
        elif type == 'jpg' or type == 'jpeg' or type == 'png':
            img_data = open("htdocs" + filename, 'rb')
            content = img_data.read()
        else:
            content = "fail"
        file.close()
        
    else:
        print("no path: htdocs" + filename)
        content = "fail"

    return content

#class ImgMsg:
 #   def __init__(self, type, content):
  #      self.header = 'Content-Type: image/'+ type + '\r\n'
   #     self.content = content

def BuildMsg(status, content, type):
    if status == 200:
        if type == 'html' or type == 'script' or type == 'css' or type == 'txt':
            response = 'HTTP/1.0 200 OK\n\n' + content
            response = response.encode()
        else:
            response = b'HTTP/1.0 200 OK\r\n'
            response += bytes("Content-Type: image/"+ type + "\r\n", "ascii")
            response += b'Accept-Ranges: bytes\r\n\r\n'
            response += content
    else:
        response = b'HTTP/1.0 404 Not Found\r\n'

    return response




while True:

    client_connection, client_address = server_socket.accept()

    request = client_connection.recv(10240).decode()
    print(request)

    #get clients requests
    headers = request.split('\n')
    filename = headers[0].split()[1]

    if filename == '/':
        filename = '/index.html'




    type = filename.split('.')[1]
    content = ReadFile(filename)
    if request[:3] == 'GET':
        if isinstance(content, str):
            if content != 'fail':

                    response = BuildMsg(200, content, type)
                    client_connection.sendall(response)

            else:
                response = BuildMsg(404, 0, 0)
                client_connection.sendall(response)
        else:
            response = BuildMsg(200, content, type)
            client_connection.sendall(response)
    elif request[:4] == 'POST':
        print("shiiiiii")
        username = request.split('username=', '&')[1]
        print(username)
    
    client_connection.close()
    




server_socket.close()

