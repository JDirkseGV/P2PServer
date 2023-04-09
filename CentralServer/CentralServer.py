import os
import socket
import sys
import time
import threading
import mimetypes
#John Dirkse Data Com Project 3 - p2p Central Server

killThreads = False
files = {}
users = {}

def main(): 
    serverIp = "localhost"
    serverPort = 10106      #my g number (0106 + 10,000)

    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        serverSocket.bind((serverIp, serverPort))     
        serverSocket.listen()                                             #sets up tcp socket to listen based on serverIp and serverPort
        print(f"{serverIp}:{serverPort} is the Central Server and is now live and listening")

        while True:
            hostSocket, hostAddr = serverSocket.accept()        #accepts connections and passes them off to their own thread
            print(f"Accepted connection from host {hostAddr[0]}:{hostAddr[1]}")
            hostThread = threading.Thread(target=hostThreadFunction, args=(hostSocket, hostAddr))
            hostThread.start()
    except KeyboardInterrupt:
        print("Server shutting down")
        killThreads = True
        hostThread.join()
        serverSocket.close() 
        print("Shut down complete")           #if control + c, close everything and exit.
        sys.exit()

def hostThreadFunction(hostSocket, hostAddr):
        
        username = hostSocket.recv(1024).decode()
        time.sleep(.1)
        connectionSpeed = hostSocket.recv(1024).decode()
        time.sleep(.1)

        numFiles = hostSocket.recv(1024).decode() #get a heads up of how many entries are coming over.
        for i in range(0, numFiles):
            time.sleep(.1)
            file = hostSocket.recv(1024).decode() #recieve filenames and descriptions
            file = file.split(",")
            file.strip()
            filename = file[0]
            description = file[1]
            hostAddr[1] += 1
            addFile(username, filename, description, connectionSpeed, hostAddr[0], hostAddr[1])

        dataPort = hostSocket.recv(1024).decode() 
        


        while not killThreads:
            dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TODO might not have to use data socket.
            command = ""
            filename = ""
            command = hostSocket.recv(1024).decode() 
            time.sleep(.5)

            match command:
                case 'QUIT': #TODO remove file entries from disconnecting host
                    print(f"Disconnecting from host {hostAddr[0]}:{hostAddr[1]}.")
                    removeFiles(username)
                    hostSocket.close()
                    return
                case 'SEARCH':
                    filename = hostSocket.recv(1024).decode()
                    dataSocket.connect((hostAddr[0], int(dataPort)))
                    searchFiles(dataSocket, filename)
                    dataSocket.close()    
        hostSocket.close() 

def addFile(username, filename, description, connectionSpeed, hostName, hostPort):
    if filename not in files:
        files[filename] = []
    files[filename].append((username, filename, description, connectionSpeed, hostName, hostPort))

def removeFiles(username):
    for filename, fileInfo in files.items():
        print(fileInfo)
        for info in fileInfo:
            print(info)
            print(f"info 0: {info[0]}")
            if username in info[0]:
                files.remove(filename)
    
def searchFiles(dataSocket, filename):
    #TODO send over host socket potentially 
    files = os.listdir(os.getcwd())
    length = str(len(files))
    dataSocket.send(length.encode()) #send amount of file names to expect
    time.sleep(.1)
    for filename in files:
        print(filename)
        dataSocket.send(filename.encode()) #send filenames
        time.sleep(.1)
    print("Successfully searched all files.")
    return

if __name__ == '__main__':
    main()