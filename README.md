# 🌐 Cidade Inteligente - Sistemas Distribuídos com Sockets
Este projeto simula uma Cidade Inteligente com sensores e atuadores que se comunicam com um Gateway central. Um aplicativo Flutter permite controle e monitoramento em tempo real.


## 🧠 O que é?

Um sistema distribuído para aprendizado de comunicação entre processos. Ele simula:

- **Dispositivos inteligentes**: sensores e atuadores que interagem com o ambiente.
- **Gateway central**: responsável pela coordenação e comunicação entre dispositivos.
- **App cliente**: interface de controle e monitoramento em tempo real.

## 🔧 Tecnologias Utilizadas

- **Python**: desenvolvimento do gateway e sensores (SDK v3.12.3).
- **Node.js**: implementação de atuadores (SDK v20.18.2).
- **Flutter/Dart**: criação do aplicativo cliente (SDK v3.27.2).
- **Sockets TCP e UDP**: comunicação entre dispositivos.
- **UDP Multicast**: descoberta de dispositivos na rede.
- **Protocol Buffers (protobuf)**: serialização de mensagens (SDK Python v6.31.1).

## 📦 Estrutura de Diretórios

```
cidade_inteligente/
├── flutter_client/               # Aplicativo Flutter
│   └── lib/
│       ├── main.dart              # Arquivo principal do app
│       ├── simulador_falhas.dart  # Simulação de falhas
│       └── protos/
│           └── mensagem.pb.dart   # Arquivo gerado pelo Protobuf
├── dispositivos/           # Código dos dispositivos inteligentes
│   ├── poste_node/         # Atuador em Node.js
│   |   └── poste.js
│   └── sensor_temp.py      # Sensor de temperatura em Python
├── exemplos/               # Code snippets
├── gateway/                # Código do Gateway em Python
│   └── gateway.py
├── protos/                 # Definições de mensagens Protobuf
│   └── messages.proto
└── README.md               # Documentação principal
```

## ▶️ Como Executar

### 1. Pré-requisitos

- Python SDK v3.12.3
- Node.js 14+ SDK v20.18.2
- Flutter SDK v3.27.2
- `protoc` (Protocol Buffers compiler / v31.1) (Python / v6.31.1)

### 2. Instalação de dependências

```bash
# Python
$ pip install protobuf

# Node.js
$ npm install protobufjs

# Flutter
$ flutter pub get
```

### 2. Gerar arquivos Protobuf

- Python
```bash
$ protoc --python_out=. protos/mensagem.proto
```

- Node.js
```bash
$ protoc --js_out=import_style=commonjs,binary:. protos/mensagem.proto
```

- Flutter
```bash
$ protoc --dart_out=flutter_client/lib/protos protos/mensagem.proto
```

### 3. Rodar os componentes (em terminais separados)
- Gateway
```bash
$ python3 gateway/gateway.py
```

- Sensor de Temperatura
```bash
$ python3 dispositivos/sensor_temp.py
```

- Atuador (Poste)
```bash
$ node dispositivos/poste_node/poste.js
```

- Aplicativo Flutter
```bash
$ cd flutter_client
$ flutter run
```
