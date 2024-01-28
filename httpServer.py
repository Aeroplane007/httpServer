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
        raise Exception("No such file")

    return content, type


def BuildMsg(status, file, client_connection):
    
    if status == 200:
        #try to read file
        try:
            content, type = ReadFile(filename)
            if type == 'html' or type == 'script' or type == 'css' or type == 'txt':
                response = 'HTTP/1.0 200 OK\n\n' + content
                response = response.encode()
                client_connection.sendall(response)
            else:
                response = b'HTTP/1.0 200 OK\r\n'
                response += bytes("Content-Type: image/"+ type + "\r\n", "ascii")
                response += b'Accept-Ranges: bytes\r\n\r\n'
                response += content
                client_connection.sendall(response)
        except:
            #if no such file exists send 404
            print("except")
            BuildMsg(404,0, client_connection)
    elif status == 403:
        response = b'HTTP/1.0 403 Forbidden\n\n'
        response += b'<html><body><h1>404 Forbidden!</h1></body></html>'
        client_connection.sendall(response)
    elif status == 600:
        content = ParseHTML(file,"<!--Invalid username-->", "<p style=\"color: red\">Invalid username or password</p>")
        response = 'HTTP/1.0 200 OK\n\n' + content
        response = response.encode()
        client_connection.sendall(response)
    elif status == 601:
        content = ParseHTML(file,"<!--User already exist-->", "<p style=\"color: red\">Username already exist</p>")
        print(content)
        response = 'HTTP/1.0 200 OK\n\n' + content
        response = response.encode()
        client_connection.sendall(response)
    else:
        print("404")
        response = b'HTTP/1.0 404 Not Found\n\n'
        response += b'<html><body><h1>404 Not Found!</h1></body></html>'
        client_connection.sendall(response)


def SetCookie(client_connection, username):
    #generate cookie id by random number
    cookie_id = secrets.token_urlsafe(16) + "$"
    
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
    if (-1)*time > 24*60:
        return False
    
    #otherwise return true
    return True
    

def ParseHTML(file, text_to_replace, replacement):
    file_data = open('htdocs/' + file)
    content = file_data.read()
    content = content.replace(text_to_replace, replacement)

    return content







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
        end_index = request.find("$")
        cookie_id = request[index+11:end_index+1]
        print("cookieees: " + cookie_id)

    if filename == '/':
        filename = '/index.html'

    type = filename.split('.')[1]

    print(filename)
    #in future, check if they have acces to the page they are trying to enter



    if request[:3] == 'GET':
        if (filename == "/login.html") and not CheckCookie(cookie_id):
            BuildMsg(403, 0, client_connection)
        else:
            print("filenameee is:" + filename)
            if (filename == "/index.html") and CheckCookie(cookie_id):
                filename = "/login.html"
            
                BuildMsg(200, filename, client_connection)

            else:
                BuildMsg(200, filename, client_connection)

 


    elif request[:4] == 'POST':
        #check if trying to login or create account
        if filename == "/login.html":
            #get username and password from post
            username = request.split('username=')[1].split('&')[0]
            password = request.split('password=')[1]

            #fetch password for user in sql
            query = "SELECT password FROM users WHERE username = %s;"
            mycursor.execute(query, (username,))
            myresults = mycursor.fetchone()
            #check if exists
            if not myresults:
                print("wrong user lol")
                BuildMsg(600,"/index.html", client_connection)
            else:
                for row in myresults:
                    myresults = row
                if password == myresults:
                    print('success')
                    SetCookie(client_connection, username)
                    BuildMsg(200, filename, client_connection)

                        
                else:
                    content = ParseHTML("index.html", "<!--Invalid username-->", "<p style=\"color: red\">Invalid username or password</p>")
                    print("wrong user lol")
                    BuildMsg(600,"/index.html", client_connection)

        else:
            username = request.split('username=')[1].split('&')[0]
            password = request.split('password=')[1]

            query = "SELECT username FROM users WHERE username = %s;"
            mycursor.execute(query, (username,))
            myresults = mycursor.fetchone()
            if not myresults:
                print("free")
                query = "INSERT INTO users (username, password) VALUES (%s,%s)"
                mycursor.execute(query, (username,password))
                db.commit()
                SetCookie(client_connection, username)
                BuildMsg(200, filename, client_connection)
            else:
                print("user already exist")
                BuildMsg(601,"create.html", client_connection)

    
    client_connection.close()
    




server_socket.close()

