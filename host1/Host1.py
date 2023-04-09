import os
import socket
import sys
import time
import threading
import random

#John Dirkse Data Com Project 2 - ftp server server

killThreads = False

def main(): 
    serverIp = "localhost"
    serverPort = 11000      #11000 for host 1

    dataIp = "localhost"
    dataPort = 4242 #randomized when setting connection up

    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        serverSocket.bind((serverIp, serverPort))     
        serverSocket.listen()                                             #sets up tcp socket to listen based on serverIp and serverPort
        print(f"{serverIp}:{serverPort} is now live and listening")
        serverThread = threading.Thread(target=serverHandlerThread, args=(serverSocket))
        serverThread.start()
        #----------------------------------------server stuff done
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        clientSocket.bind((serverIp, (serverPort-1))) #connect over port serverPort-1 aka 10999 so that Central server knows 11000 is server port where file can be retrieved.
        dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dataPort = random.randint(1025, 65534)
        dataSocket.bind((dataIp, dataPort))
        dataSocket.listen()
        restart = True
        

        while True:
            if restart:
                print("----------------------------\nWelcome to FTP Client! Connect to the central server with:\n[CONNECT <server ip/hostname> <server port>]")   
            else:
                print("-----------------------------\nCommands:\n[LS]\n[LIST]\n[RETR <filename>]\n[STOR <filename>]\n[QUIT]")
            command = input('Enter a command: ')
            arguments = command.split()
            arguments = [command.strip() for command in arguments]
            if len(arguments) > 0:
                match arguments[0].upper(): #Mom get the camera! It only took until python 3.10 for them to add switch statements!
                    case 'LS':
                        print(os.listdir(os.getcwd()))
                    case 'CONNECT':
                        if len(arguments) == 3:
                            serverLocation = arguments[1]
                            serverPort = int(arguments[2])
                            print("Trying to connect to server...")
                            clientSocket.connect((serverLocation, serverPort))
                            dataPort = str(dataPort)
                            clientSocket.send(dataPort.encode()) #let server know info for data transfer socket setup in the future.
                            dataPort = int(dataPort)
                            print("Connection sucess!")
                            restart = False
                        else:
                            print("CONNECT requires format: CONNECT <server ip> <server port> and takes 2 arguments. Please try again.")
                    case 'LIST':
                        listFiles(clientSocket, dataSocket)
                    case 'RETR':
                        if len(arguments) == 2:
                            filename = arguments[1] #In the wise words of Kurmas: "If a couple extra keystrokes helps untie some knots in your head, then they are keystrokes well spent"
                            retrieveFiles(clientSocket, dataSocket, filename)
                        else:
                            print("RETR requires format: RETR <filename> and takes 1 argument. Please try again.")                        
                    case 'STOR':
                        if len(arguments) == 2:
                            filename = arguments[1]
                            storeFiles(clientSocket, dataSocket, filename)
                        else:
                            print("STOR requires format: STOR <filename> and takes 1 argument. Please try again.")     
                    case 'QUIT':
                        print("Client closing server thread and shutting down")
                        clientSocket.send("QUIT".encode())
                        clientSocket.close()
                        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        restart = True
            else:
                print("Please enter an argument and try again.")
        
    except KeyboardInterrupt:
        print("Host shutting down")
        killThreads = True
        serverThread.join()
        serverSocket.close() 
        clientSocket.close()
        print("Shut down complete")           #if control + c, close everything and exit.
        sys.exit()


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
                case 'LIST':
                    dataSocket.connect((clientAddr[0], int(dataPort)))
                    listFiles(dataSocket)
                    dataSocket.close()
                case 'RETR': 
                    filename = clientSocket.recv(1024).decode()
                    dataSocket.connect((clientAddr[0], int(dataPort)))
                    retrieveFiles(dataSocket, filename)   
                    dataSocket.close()                
                case 'STOR':
                    filename = clientSocket.recv(1024).decode()
                    dataSocket.connect((clientAddr[0], int(dataPort)))
                    storeFiles(dataSocket, filename)
                    dataSocket.close()     
        clientSocket.close() 

def listFiles(dataSocket):
    print("Listing files for client...")
    files = os.listdir(os.getcwd())
    length = str(len(files))
    dataSocket.send(length.encode()) #send amount of file names to expect
    time.sleep(.1)
    for filename in files:
        print(filename)
        dataSocket.send(filename.encode()) #send filenames
        time.sleep(.1)
    print("Successfully listed all files.")
    return

def retrieveFiles(dataSocket, filename):  
    print("Attempting to send " +filename + "...")
    if os.path.isfile(filename):
        print(filename + " found")
        fileSize = str(os.path.getsize(filename))
        dataSocket.send(fileSize.encode())
        time.sleep(.5)
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

def storeFiles(dataSocket, filename):
    fileSize = int(dataSocket.recv(1024).decode())
    if fileSize == -1:
        print("File not coming.")
    else:
        print("File found, downloading and writing to disk...")
        newFile = open(filename, "wb")
        currentBytes = 0
        while currentBytes < fileSize:
            chunk = dataSocket.recv(1024)
            newFile.write(chunk)
            currentBytes += 1024
        newFile.close()
        print("File retrieval finished.")
    return

if __name__ == '__main__':
    main()
