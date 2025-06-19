import socket

MCAST_GRP = '228.0.0.8'
MCAST_PORT = 6789
msg = 'Paulo!!!!!!!!!'
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((MCAST_GRP, MCAST_PORT))
sock.sendto(bytes(msg, 'utf-8'), (MCAST_GRP, MCAST_PORT))
print(sock.recv(10240).decode('utf-8'))
sock.close()
