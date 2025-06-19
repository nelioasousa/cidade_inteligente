import socket

i = 0
HOST = ''
PORT = 6789
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
while True:
    i += 1
    print("Esperando Msg {s} ...".format(s=i))
    data, address = sock.recvfrom(1024)
    h, p = address
    print("Cliente: {s} - Porta: {t}\nMsg: {u}".format(s=h, t=p, u=data.decode('utf-8')))