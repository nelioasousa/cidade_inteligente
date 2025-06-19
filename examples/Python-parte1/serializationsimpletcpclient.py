import socket, pickle

from pessoa import Pessoa
HOST = 'localhost'
PORT = 6789
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
pessoa = Pessoa("Joao da Silva", 'Quixada', '999990000', '2014')
print(pessoa.toString())
data_string = pickle.dumps(pessoa)
s.sendall(data_string)
data = s.recv(1024)
pessoa = pickle.loads(data)
print(pessoa.toString())
s.close()