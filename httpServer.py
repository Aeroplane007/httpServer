import socket
import imageio
import os
import ssl
import mysql.connector
import secrets
import time
import datetime


#Fix cookies
#fix security so that only one withj vlaid cookies id can enter pages other than index.html or createuser.html

#host ip and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080

#database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="root",
    database="userdata"
)

mycursor = db.cursor()
sqlquery = "SELECT password FROM users WHERE username = %s;"

#mycursor.execute(sqlquery)
#db.commit()

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
    elif status == 403:
        response = 'HTTP/1.0 403 Forbidden\n\n'
        response += '<html><body><h1>403 Forbidden!</h1></body></html>'
        response = response.encode()
    else:
        response = b'HTTP/1.0 404 Not Found\r\n'

    return response

def SetCookie(client_connection, username):
    #generate cookie id by random number
    cookie_id = secrets.token_urlsafe(16) + "AAA"
    
    #send cookie to user
    response = 'HTTP/1.0 200 OK\r\n'
    response += 'Content-Type: text/html\r\n'
    response += 'Set-Cookie: id='+ cookie_id +'\r\n'
    response = response.encode()
    client_connection.sendall(response)

    #save cookie in database as session id
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = "UPDATE users SET cookie_id = %s, cookie_time = %s WHERE username = %s"
    print(username)
    print(cookie_id)
    mycursor.execute(query, (cookie_id, timestamp, username))
    db.commit()

def CheckCookie(cookie_id):

    print("checking cookise")
    #check if cookie_id exists in the table
    query = "SELECT cookie_id FROM users WHERE cookie_id = %s;"
    mycursor.execute(query, (cookie_id,))
    print((cookie_id,))
    id = mycursor.fetchone()
    print(id)
    if not id:
        return False
    #get time since cookie_id was last updated
    query = "SELECT TIMESTAMPDIFF(MINUTE, NOW(), cookie_time) FROM users WHERE cookie_id = %s;"
    mycursor.execute(query,(cookie_id,))
    time = mycursor.fetchone()
    print(time)
    for t in time:
        time = t
    print(time)
    #if it was too many minutes ago(one day) return false
    if -time > 24*60:
        return False
    
    #otherwise return true
    return True
    

def ParseHTML(file, text_to_replace, replacement):
    file_data = ReadFile("file")
    








while True:

    client_connection, client_address = server_socket.accept()
    cookie_id = "0"

    request = client_connection.recv(10240).decode()
    print(request)


    #get clients requests
    headers = request.split('\n')
    print(headers)

    filename = headers[0].split()[1]
    if 'Cookie' in request:
        index = request.find("Cookie: id=")
        end_index = request.find("AAA")
        cookie_id = request[index+11:end_index+3]
        print("cookieees: " + cookie_id)

    if filename == '/':
        filename = '/index.html'

    type = filename.split('.')[1]

    print(filename)
    #in future, check if they have acces to the page they are trying to enter



    if request[:3] == 'GET':
        if (filename == "/login.html") and not CheckCookie(cookie_id):
            response = BuildMsg(403, 0, 0)
            client_connection.sendall(response)
        else:
            if (filename == "/index.html") and CheckCookie(cookie_id):
                filename = "/login.html"
            content = ReadFile(filename)
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
        username = request.split('username=')[1].split('&')[0]
        password = request.split('password=')[1]
        print(username + "   " + password)
        mycursor.execute(sqlquery, (username,))
        myresults = mycursor.fetchone()
        if not myresults:
            response = BuildMsg(600,0,0)
            ParseHTML("index.html", "<!--Invalid username-->", "<p style="color: red">Invalid username or password</p>")
        for row in myresults:
           myresults = row
        if password == myresults:
            print('success')
            SetCookie(client_connection, username)
            response = BuildMsg(200, content, type)
            client_connection.sendall(response)
                
        else:
            content = ReadFile("/logfail.html")
            response = BuildMsg(200, content, type)
            client_connection.sendall(response)
    
    client_connection.close()
    




server_socket.close()

