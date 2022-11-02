from asyncore import write
import socket, select, string, sys

from pandas import array

#Helper function (formatting)
def display() :
	you="\33[33m\33[1m"+" You: "+"\33[0m"
	sys.stdout.write(you)
	sys.stdout.flush()

def main():
    list_of_message = []
    if len(sys.argv)<2:
        host = input("Enter host ip address: ")
    else:
        host = sys.argv[1]

    port = 5000
    
    #asks for user name
    name=input("\33[34m\33[1m CREATING NEW ID:\n Enter username: \33[0m")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    
    # connecting host
    try :
        s.connect((host, port))
    except :
        print("\33[31m\33[1m Can't connect to the server \33[0m")
        sys.exit()

    #if connected
    s.send(str.encode(name))
    display()
    while 1:
        socket_list = [sys.stdin, s]
        
        # Get the list of sockets which are readable
        rList, wList, error_list = select.select(socket_list , [], [])
        
        for sock in rList:
            #incoming message from server
            if sock == s:
                data = sock.recv(4096)
                if not data :
                    print('\33[31m\33[1m \rDISCONNECTED!!\n \33[0m')
                    sys.exit()
                else :
                    if('-'in data.decode()):
                        list_of_message.append(data.decode())
                    else:
                        (sys.stdout.write(data.decode()))
                        display()
        
            #user entered a message
            else :
                msg=sys.stdin.readline()

                array = msg.split('-')
                if(array[0].strip() == "read"):
                    to_read = array[1].strip()
                    if(to_read=="all"):
                        for message in list_of_message:
                            print(message)
                            list_of_message.remove(message)
                    else:
                        for message in list_of_message:
                            if(message.split('-')[0].strip()==to_read):
                                print(message)
                                list_of_message.remove(message)  
                    display()               
                else:
                    s.send(str.encode(msg))
                    display()

if __name__ == "__main__":
    main()