import os
import socket
import sys
import time
import threading

import random

#John Dirkse Data Com Project 3 - p2p host

killThreads = False
sendDelay = .15

def main(): 
    hostIp = "localhost"
    serverPort = 11000      #11000 for host 1
    hostDataPort = 4243 #host to host data port randomized when setting connection up

    centralIp = "localhost"
    centralDataPort = 4234 #central server to host port randomized and passed when setting connection up

    try:
        #serverSocket and server thread setup
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        serverSocket.bind((hostIp, serverPort))     
        serverSocket.listen()                                             #sets up tcp socket to listen based on hostIp and serverPort
        print(f"{hostIp}:{serverPort} is now live and listening")
        serverThread = threading.Thread(target=serverHandlerThread, args=(serverSocket,))
        serverThread.start()

        #---------------------------------------- centralSocket for persistent central server connection
        centralSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #---------------------centralDataSocket for central to host data
        centralDataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        centralDataPort = random.randint(1025, 65534)
        centralDataSocket.bind((centralIp, centralDataPort))
        centralDataSocket.listen()

        #-------------------------------------- data socket for host to host

        hostDataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostDataPort = random.randint(1025, 65534)
        hostDataSocket.bind((hostIp, hostDataPort))
        hostDataSocket.listen()
        restart = True
        

        while True:
            hostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if restart:
                print("----------------------------\nWelcome to P2P Host! Connect to the central server with:\n[CONNECT <server ip/hostname> <server port>]")   
            else:
                print("-----------------------------\nCommands:\n[LS]\n[SEARCH <keyword>]\n[GET <filename>]\n[QUIT]")
            command = input('Enter a command: ')
            arguments = command.split()
            arguments = [command.strip() for command in arguments]
            if len(arguments) > 0:
                match arguments[0].upper(): #Mom get the camera! It only took until python 3.10 for them to add switch statements!
                    case 'LS':
                        print(os.listdir(os.getcwd()))
                    case 'CONNECT': #TODO connect rework, 1 for central one for p2p
                        if len(arguments) == 3:
                            serverLocation = arguments[1]
                            centralServerPort = int(arguments[2])
                            print("Trying to connect to server...")
                            centralSocket.connect((serverLocation, centralServerPort))

                            centralDataPort = str(centralDataPort)
                            centralSocket.send(centralDataPort.encode()) #let server know info for data transfer socket setup in the future.
                            centralDataPort = int(centralDataPort)

                            time.sleep(sendDelay)
                            centralSocket.send(str(serverPort).encode())

                            
                            username = input("Please enter your username: ")
                            time.sleep(sendDelay)
                            centralSocket.send(username.encode())
                            
                            speed = input("Please enter your connection speed: ")
                            time.sleep(sendDelay)
                            centralSocket.send(speed.encode())
                            
                            time.sleep(sendDelay)
                            with open("sharedFiles.txt", "r") as file:
                                for line in file:
                                    cleanLine = line.strip()
                                    print(cleanLine)
                                    centralSocket.send(cleanLine.encode())
                                    time.sleep(sendDelay)

                            print("Connection sucess!")
                            restart = False
                        else:
                            print("CONNECT requires format: CONNECT <server ip> <server port> and takes 2 arguments. Please try again.")
                    case 'SEARCH':
                        if len(arguments) == 2:
                            keyword = arguments[1]
                            searchFiles(keyword)
                            return
                        else:
                            print("SEARCH requires format: SEARCH <keyword> and takes 1 argument. Please try again.") 
                    case 'GET':
                        if len(arguments) == 2:
                            filename = arguments[1] #In the wise words of Kurmas: "If a couple extra keystrokes helps untie some knots in your head, then they are keystrokes well spent"
                            retrieveFiles(centralSocket, centralDataSocket, filename, hostSocket, hostDataSocket)
                        else:
                            print("GET requires format: GET <filename> and takes 1 argument. Please try again.")                             
                    case 'QUIT':
                        print("Client closing server thread and shutting down")
                        centralSocket.send("QUIT".encode())
                        centralSocket.close()
                        centralSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        restart = True
            else:
                print("Please enter an argument and try again.")
        
    except KeyboardInterrupt:
        print("Host shutting down")
        killThreads = True
        serverThread.join()
        serverSocket.close() 
        centralSocket.close()
        print("Shut down complete")           #if control + c, close everything and exit.
        sys.exit()

def searchFiles(centralSocket, centralDataSocket, searchTerm):
    #TODO: get file entries from centralserver
    return

def retrieveFiles(centralSocket, centralDataSocket, filename, hostSocket, hostDataSocket):
    #TODO: get ip/port from central, then set up connection with other host

    centralSocket.send("GET".encode())
    time.sleep(sendDelay)
    centralSocket.send(filename.encode())
    dataConnection, serverAdr = centralDataSocket.accept()
    fileSize = int(dataConnection.recv(1024).decode())
    if fileSize == -1:
        print("File not readable, make sure you have the right filename and try again.")
    else:
        print("File found, downloading and writing to disk...")
        newFile = open(filename, "wb")
        currentBytes = 0
        while currentBytes < fileSize:
            chunk = dataConnection.recv(1024)
            newFile.write(chunk)
            currentBytes += 1024
        newFile.close()
        print("File retrieval finished.")
    dataConnection.close()
    return


def serverHandlerThread(serverSocket):
    while True:
            clientSocket, clientAddr = serverSocket.accept()        #accepts connections and passes them off to their own thread
            print(f"Accepted connection from {clientAddr[0]}:{clientAddr[1]}")
            clientThread = threading.Thread(target=clientThreadFunction, args=(clientSocket, clientAddr))
            clientThread.start()

def clientThreadFunction(clientSocket, clientAddr):
    
        dataPort = clientSocket.recv(1024).decode() 

        while not killThreads:
            dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            command = ""
            filename = ""
            command = clientSocket.recv(1024).decode() 
            #print(f"[{clientAddr[0]}:{clientAddr[1]}]\n{command}")

            match command:
                case 'QUIT':
                    print("Disconnecting from client.")
                    clientSocket.close()
                    return
                case 'GET': 
                    filename = clientSocket.recv(1024).decode()
                    dataSocket.connect((clientAddr[0], int(dataPort)))
                    sendFiles(dataSocket, filename)   
                    dataSocket.close()                  
        clientSocket.close() 

def sendFiles(dataSocket, filename):  
    print("Attempting to send " +filename + "...")
    if os.path.isfile(filename):
        print(filename + " found")
        fileSize = str(os.path.getsize(filename))
        dataSocket.send(fileSize.encode())
        time.sleep(sendDelay)
        file = open(filename, "rb")
        chunk = file.read(1024)
        while chunk:
            dataSocket.send(chunk)
            chunk = file.read(1024)
        file.close()
        print(filename + " sending completed")
    else:
        print(filename + " does not exist.")
        dataSocket.send("-1".encode())
    return

if __name__ == '__main__':
    main()
