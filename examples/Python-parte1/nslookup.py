import socket
site = "globo.com"
try:
    ip = socket.gethostbyname(site)
    print(ip)
except:
    print("Endereço não encontrado")