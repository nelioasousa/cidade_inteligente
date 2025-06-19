import socket, pickle

HOST = 'localhost'
PORT = 6789
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()

data = conn.recv(4096)
pessoa = pickle.loads(data)
pessoa.cidade = "Fortaleza"
pessoa.ano = '2019'
data_string = pickle.dumps(pessoa)
conn.sendall(data_string)
conn.close()