import socket
import imageio
import os
import ssl
import mysql.connector
import secrets
import time
import datetime
import hashlib
import json

#   Internal status codes
# 600: Wrong password or username
# 601: user already exists
# 602: noone by that username
#

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


class client():

    def __init__(self, connection, cookie_id: str , receiver=""):
        self.connection = connection
        self.cookie_id = cookie_id
        self.receiver = receiver

    def SetReceiver(self, receiver):
        self.receiver = receiver

    def SetCookie(self, cookie):
        self.cookie_id = cookie




    def GetReceiver(self):
        return self.receiver
        
    def GetConnection(self):
        return self.connection
    
    def GetCookie(self):
        return self.cookie_id
    

    



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

def GetUser(client: client):
    query = "SELECT username FROM users WHERE cookie_id = %s;"
    print("cookie", client.GetCookie())
    mycursor.execute(query, (client.GetCookie(),))
    user = mycursor.fetchone()
    return user[0]


def GetFriendHash(client: client):
    user = GetUser(client)
    users = sorted([user,client.GetReceiver()])
    hash = hashlib.sha256(bytes((users[0]+users[1]).encode())).hexdigest()

    return hash

def AddFriend(client):
    #get user
    print("Adding user")
    user = GetUser(client)
    hash = GetFriendHash(client)
    query = "SELECT * FROM friends WHERE FriendsId = %s;"
    mycursor.execute(query, (hash,))
    result = mycursor.fetchone()
    #check so not friends
    if not result:
        query = "INSERT INTO friends (FriendsId, UserOne, UserTwo, Status) VALUES (%s,%s,%s,%s)"
        mycursor.execute(query, (hash, user, client.GetReceiver(), -1))
        db.commit()
    else:
        print("already friends")



def GetFriends(client: client):

    user = GetUser(client)
    print("Get friends for: " + user)
    query = "SELECT UserOne,UserTwo FROM friends WHERE UserOne = %s OR UserTwo = %s;"

    mycursor.execute(query, (user,user))
    usernames = mycursor.fetchall()
    friends = []
    #check if no friends
    if not usernames:
        return ""
    for u in usernames:
        if u[0] == user:
            friends.append(u[1])
        else:
            friends.append(u[0])

    print(friends)
    return friends


def GetMessages(client: client):
    user = GetUser(client)
    print("hash")
    hash = GetFriendHash(client)

    #Get last message
    query = "SELECT Sender, LastMessage FROM last_message WHERE ChatId = %s"
    print(hash)
    mycursor.execute(query, (hash,))
    senders = []
    messages = []
    msg = mycursor.fetchone()
    print(msg)
    #check if no msg
    if not msg:
        return "none", "none"
    senders.append(msg[0])
    messages.append(msg[1])
    print("last message: ", messages)

    #Get last 10 messages
    query = "SELECT Sender, Message FROM messages WHERE ChatId = %s ORDER BY TimeStamp DESC LIMIT 10"
    mycursor.execute(query, (hash,))
    result = mycursor.fetchall()
    #if not other messages
    if not result:
        return messages, senders
    for msg in result:
        senders.append(msg[0])
        messages.append(msg[1])

    return messages, senders

def GetNewMessages(client: client, time_since):
    #convert to datetime
    user = GetUser(client)
    time_since = datetime.datetime.fromtimestamp(time_since//1000)
    hash = GetFriendHash(client)
    print(time_since)
    print(hash)
    query = "SELECT TIMESTAMPDIFF(SECOND, %s, TimeStamp) FROM last_message WHERE ChatId= %s"
    mycursor.execute(query, (time_since,hash))
    time_diff = mycursor.fetchone()
    print("time diff: ", time_diff)
    #check if there is a message
    if not time_diff:
        return []
    messages = []
    if time_diff[0] > 0:
        
        query = "SELECT  Sender, LastMessage FROM last_message WHERE ChatId = %s"
        mycursor.execute(query, (hash,))
        msg = mycursor.fetchone()
        if msg[0] != user:
            messages.append(msg[1])
        
        query = "SELECT Sender, Message FROM messages WHERE ChatId = %s and TIMESTAMPDIFF(SECOND, %s, TimeStamp) > 0"
        mycursor.execute(query, (hash, time_since))
        msgs = mycursor.fetchall()
        for msg in msgs:
            if msg[0] != user:
                messages.append(msg[1])
    return messages




def BuildMsg(status, filename, client: client, parameters={}):
    
    if status == 200:
        #try to read file
        try:
            content, type = ReadFile(filename)
            print(filename)
            if type == 'html' or type == 'script' or type == 'css' or type == 'txt':
                content = ParseHTML(filename,client,0)
                response = 'HTTP/1.0 200 OK\n\n' + content
                response = response.encode()
                client.GetConnection().sendall(response)
            else:
                response = b'HTTP/1.0 200 OK\r\n'
                response += bytes("Content-Type: image/"+ type + "\r\n", "ascii")
                response += b'Accept-Ranges: bytes\r\n\r\n'
                response += content
                client.GetConnection().sendall(response)
        except: #Exception as e: print(e)
            #if no such file exists send 404
            print("CAUGT EXCEPTION")
            BuildMsg(404,0, client, 0)
    elif status == 403:
        response = b'HTTP/1.0 403 Forbidden\n\n'
        response += b'<html><body><h1>404 Forbidden!</h1></body></html>'
        client.GetConnection().sendall(response)
    elif status == 600:
        content = ParseHTML(filename,client, 600)
        response = 'HTTP/1.0 200 OK\n\n' + content
        response = response.encode()
        client.GetConnection().sendall(response)
    elif status == 601:
        content = ParseHTML(filename, client, 601)
        response = 'HTTP/1.0 200 OK\n\n' + content
        response = response.encode()
        client.GetConnection().sendall(response)
    elif status == 602:
        print("geting new msgs")
        #Get New Messages
        new_messages = GetNewMessages(client, parameters["Time"])
        response = "none"
        if len(new_messages) > 0:
            json_message = {"messages": new_messages}
            json_string = json.dumps(json_message, indent=2)
            response = json_string
        print(response)
        response = response.encode()
        client.GetConnection().sendall(response)
    else:
        print("404")
        response = b'HTTP/1.0 404 Not Found\n\n'
        response += b'<html><body><h1>404 Not Found!</h1></body></html>'
        client.GetConnection().sendall(response)


def SetCookie(client: client, username):
    #generate cookie id by random number
    cookie_id = secrets.token_urlsafe(16) + "$"
    
    #send cookie to user
    response = 'HTTP/1.0 200 OK\r\n'
    response += 'Content-Type: text/html\r\n'
    response += 'Set-Cookie: id='+ cookie_id +'\r\n'
    response = response.encode()
    client.GetConnection().sendall(response)

    #save cookie in database as session id
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = "UPDATE users SET cookie_id = %s, cookie_time = %s WHERE username = %s"
    print(username)
    print(cookie_id)
    mycursor.execute(query, (cookie_id, timestamp, username))
    db.commit()

    return cookie_id

def CheckCookie(client: client):

    print("cookie client", client.GetCookie())
    #check if cookie_id exists in the table
    query = "SELECT cookie_id FROM users WHERE cookie_id = %s;"
    mycursor.execute(query, (client.GetCookie(),))
    
 
    id = mycursor.fetchone()

    if not id:
        return False
    #get time since cookie_id was last updated
    query = "SELECT TIMESTAMPDIFF(MINUTE, NOW(), cookie_time) FROM users WHERE cookie_id = %s;"
    mycursor.execute(query,(client.GetCookie(),))
    time = mycursor.fetchall()[0]
    for t in time:
        time = t

    #if it was too many minutes ago(one day) return false
    if (-1)*time > 24*60:
        return False
    
    #otherwise return true
    return True
    
def AreFriends(client: client):
    hash = GetFriendHash(client)
    query = "SELECT * FROM friends WHERE FriendsId = %s"
    mycursor.execute(query, (hash,))
    result = mycursor.fetchone()
    if not result:
        return False
    return True


def ParseHTML(file, client: client, error_code):
    text_to_replace = ""
    replacement = ""

    #read file
    file_data = open('htdocs' + file)
    content = file_data.read()
    tags = []
    print("parsing:", error_code, " file: ", file)

    #look for comments of type <!--? ?-->
    for i in range(0, len(content)-4, 1):
        if(content[i:i+5] == "<!--?"):
            ptr1 = i
        if(content[i:i+4] == "?-->"):
            ptr2 = i+4
            tags.append(content[ptr1:ptr2])
    
    if tags is None:
        print("is none")
        return content
    #replace with correct     
    print(tags)   
    for a in tags:
        if a == "<!--?Friends?-->":
            print("friends")
            text_to_replace = "<!--?Friends?-->"
            friends = GetFriends(client)
            friend_list = ""
            for f in friends:
                friend_list += "<form id=\"friend-box\" action=\"/chat.html\" method=\"POST\"><input type=\"submit\" name=\"Chat\" value=\"" + f + "\"></form>\n"
            replacement = friend_list

        elif a == "<!--?Messages?-->":
            text_to_replace = "<!--?Messages?-->"
            print("GetMessages")
            messages, senders = GetMessages(client)
            if messages == "none":
                continue
            html_msgs = ""
            for i in range(len(messages)-1, -1, -1):
                #check if from me or friend
                if senders[i] ==  GetUser(client): 
                    html_msgs += "<div class=\"message user-message\">" + messages[i] + "</div>"
                else:
                    html_msgs += "<div class=\"message bot-message\">" + messages[i] + "</div>"

                replacement = html_msgs
            #messages, sender = GetMessages(cookie_id, receiver)
        #check if error has occured
        elif a == "<!--?Invalid username?-->" and error_code == 600:
            text_to_replace = "<!--?Invalid username?-->"
            replacement = "<p style=\"color: red\">Invalid username or password</p>"
        elif a == "<!--?receiver?-->":
            text_to_replace = "<!--?receiver?-->"
            replacement = "<p id=\"name\">" + client.GetReceiver() + "</p>"
        #check if error has occured
        
        elif a == "<!--?User already exist?-->" and error_code == 601:
            print("ruinginin")
            text_to_replace = "<!--?User already exist?-->"
            replacement = "<p style=\"color: red; margin-left:5%;\">Username already exist</p>"


        content = content.replace(text_to_replace, replacement)
    print("doneparsing")
    return content



def StoreMessage(message, client: client):
    user = GetUser(client)
    #get user hash
    hash = GetFriendHash(client)
    #Move last message to message table
    query = "INSERT INTO messages SELECT * FROM last_message WHERE ChatId = %s"
    mycursor.execute(query, (hash,))
    db.commit()
    #Remove last message
    query = "DELETE FROM last_message WHERE ChatId = %s"
    mycursor.execute(query, (hash,))
    db.commit()
    #insert this message into last message
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    query = "INSERT INTO last_message (ChatId,Sender,Receiver,LastMessage,TimeStamp) VALUES (%s,%s,%s,%s,%s)"
    mycursor.execute(query, (hash,user,client.GetReceiver(),message,timestamp))
    db.commit()





while True:

    new_connection, client_address = server_socket.accept()
    

    client_connection = client(new_connection, "0")


    request = client_connection.GetConnection().recv(10240).decode()
    print(request)


    #get clients requests
    headers = request.split('\n')
    headers[0] = headers[0].split("HTTP")[0]
    if '.' in headers[0]:
        filename = headers[0].split()[1]
        type = filename.split('.')[1]
        
    elif '?' in headers[0]:
        filename = headers[0].split()[1].split("?")[0]
        type = ""
        
    else:
        filename = "/"
        type = ""
        print("Error occured, sent to start page")

    if 'Cookie' in request:
            index = request.find("Cookie: id=")
            end_index = request.find("$")
            cookie_id = request[index+11:end_index+1]
            client_connection.SetCookie(cookie_id)
            print("cookieees: " + cookie_id)

    if filename == '/':
        filename = '/index.html'
        type = filename.split('.')[1]

    

    print(filename)




    if request[:3] == 'GET':
        #if trying to access login without being logged in send to index.html
        if (filename == "/login.html" or filename == "/chat.html") and not CheckCookie(client_connection):
            BuildMsg(403, 0, client_connection)
        elif filename == "/getnewchats" and CheckCookie(client_connection):
            #Get name of receiver
            chat_name = headers[0].split()[1].split("?")[1].split("&")[0].split("=")[1]
            time_since = int(headers[0].split()[1].split("?")[1].split("&")[1].split("=")[1])
            print(time_since)
            client_connection.SetReceiver(chat_name)
            #check if they are friends
            if AreFriends(client_connection):
                BuildMsg(602, 0, client_connection, {"Time": time_since})

        else:
            if (filename == "/index.html") and CheckCookie(client_connection):

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

            #check if user existexists
            if not myresults:
                BuildMsg(600, "/index.html", client_connection)
            else:
                for row in myresults:
                    myresults = row
                #check if correct password
                if password == myresults:
                    print('success')
                    client_connection.SetCookie(SetCookie(client_connection, username))
                    BuildMsg(200, filename, client_connection)

                        
                else:
                    print("Wrong user")
                    BuildMsg(600, "/index.html", client_connection)

        #add friend
        elif filename == "/adduser.html":
            username_to_add = request.split('AddUser=')[1]
            query = "SELECT username FROM users WHERE username = %s;"
            mycursor.execute(query, (username_to_add,))
            myresults = mycursor.fetchone()

            if not myresults:
                print("No one by that name: " + username_to_add)
                BuildMsg(200, "/login.html", client_connection)
            else:
                print("add user")
                client_connection.SetReceiver(username_to_add)
                AddFriend(client_connection)
                BuildMsg(200, filename, client_connection)

        #create user
        elif filename == "/newuser.html":
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
                client_connection.SetCookie(SetCookie(client_connection, username))
                BuildMsg(200, filename, client_connection, 0)
            else:
                print("user already exist")
                BuildMsg(601, "/create.html", client_connection)
        #go to chat with user
        elif filename == "/chat.html":
            chat_name = request.split('Chat=')[1]
            client_connection.SetReceiver(chat_name)
            #GetMessages
            BuildMsg(200, filename, client_connection)

        
        elif filename == "/newchat.html":
            message = request.split("body\":\"")[1][:-2]
            receiver = request.split("userId\":\"")[1].split("\",\"body")[0]
            client_connection.SetReceiver(receiver)
            StoreMessage(message, client_connection)
        else:
            print("unknown post command")

    
    client_connection.GetConnection().close()
    



