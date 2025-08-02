# 🌐 Cidade Inteligente
Este projeto simula uma Cidade Inteligente composta por sensores, atuadores e clientes, todos interconectados por meio de um Gateway central. O objetivo é fornecer uma base prática para o estudo de sistemas distribuídos e redes de comunicação.

Clientes interagem com o sistema exclusivamente por meio do Gateway, que atua como intermediário para monitoramento, controle e consumo de dados dos dispositivos inteligentes.


## 🧱 Evolução do Projeto
- **Versão 1**

Dispositivos e clientes se comunicam diretamente com o Gateway por meio de sockets e mensagens serializadas usando Protocol Buffers (protobuf).

- **Versão 2**

Foi introduzido um Message Broker (RabbitMQ) entre sensores e Gateway, promovendo uma comunicação assíncrona e desacoplada.

A comunicação com os atuadores foi (será) migrada de protobuf puro para gRPC.

Também foi desenvolvida uma Web API que permite o acesso de clientes ao sistema via HTTP. A comunicação original (sockets + protobuf) foi mantida por questões de retrocompatibilidade.

As mensagens trafegadas via RabbitMQ continuam a ser serializadas usando protobuf.


## 🧠 Componentes

#### 🔌 **Dispositivos Inteligentes**

Sensores e atuadores responsáveis por monitorar e interagir com o ambiente físico.

#### 🧠 **Gateway Central**

Núcleo do sistema que coordena as interações entre dispositivos e clientes, atuando como ponto de integração e roteamento.

#### 📨 **Message Broker (RabbitMQ)**

Intermediário entre sensores e o gateway, proporcionando comunicação assíncrona e desacoplada.

🖥️ **Clientes**

Interface para monitoramento e controle dos dispositivos em tempo real.

## 🔧 Tecnologias Utilizadas

**Ubuntu 24.04:** sistema operacional base. Os sockets foram configurados visando compatibilidade com ambientes Unix.

**Python 3.12.3:** linguagem base utilizada nos nós do sistema.

**Sockets TCP e UDP:** base para a comunicação direta entre dispositivos.

**UDP Multicast:** mecanismo usado para descoberta automática do Gateway e Broker por parte dos dispositivos inteligentes.

**Protocol Buffers:** protocolo de serialização utilizado na comunicação entre componentes distribuídos.

**RabbitMQ:** message broker para desacoplamento da comunicação Sensores-Gateway.


## 📦 Estrutura de Diretórios

```
cidade_inteligente/
├── clients/
│   └── simple_client/      # Cliente CLI
├── devices/                # Dispositivos inteligentes
│   ├── semaphore/          # Semáforo
│   └── temp_sensor/        # Sensor de temperatura
├── gateway/                # Gateway
|   ├── db/                      # Banco de dados usando SQLAlchemy + SQLite
|   ├── actuators_handler.py     # Módulo responsável pelos atuadores
|   ├── api.py                   # Web API
|   ├── clients_handler.py       # Módulo responsável pelos clientes
|   ├── config.yaml              # Arquivo de configuração do Gateway
│   ├── gateway.py               # Entry-point do Gateway
|   ├── registration_handler.py  # Módulo responsável pelo multicast e registro de dispostivos
|   ├── requirements.txt         # Lista de dependência do Gateway
|   └── sensors_handler.py       # Módulo responsável pelos sensores
├── protos/                 
│   └── messages.proto       # Mensagens do Protobuf
└── README.md                # Documentação principal
```


## ▶️ Como Executar

### 1. Compilar o arquivo de mensagens

```bash
$ cd protos/
$ protoc --version
libprotoc 31.1
# Python
$ protoc --python_out=. --pyi_out=. messages.proto
$ cp -f messages_pb2.py* ../gateway/
$ cp -f messages_pb2.py* ../devices/semaphore/
$ cp -f messages_pb2.py* ../devices/temp_sensor/
$ cp -f messages_pb2.py* ../clients/simple_client/
```

### 2. Rodar os componentes

**Broker**

```bash
$ docker run --rm --name rabbitmq --hostname rmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management
```

**Gateway**

```bash
$ cd cidade_inteligente/gateway/
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ python gateway.py --help
usage: gateway.py [-h] [-l {DEBUG,INFO,WARN,ERROR}] [-c]

Gateway central.

options:
  -h, --help            show this help message and exit
  -l {DEBUG,INFO,WARN,ERROR}, --level {DEBUG,INFO,WARN,ERROR}
                        Nível do logging.
  -c, --clear           Limpar o banco de dados ao iniciar.
(venv) $ python gateway.py --clear
```

**Semáforo**

```bash
$ cd cidade_inteligente/devices/semaphore/
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ python semaphore.py --help
usage: semaphore.py [-h] [--id ID] [--port PORT] [--multicast_ip MULTICAST_IP] [--multicast_port MULTICAST_PORT] [--disconnect_after DISCONNECT_AFTER]
                    [-l {DEBUG,INFO,WARN,ERROR}]

Simulador de semáforo.

options:
  -h, --help            show this help message and exit
  --id ID               Id que unicamente identifica o semáforo.
  --port PORT           Porta na qual o Gateway envia comandos ao atuador.
  --multicast_ip MULTICAST_IP
                        IP multicast para descobrimento do Gateway.
  --multicast_port MULTICAST_PORT
                        Porta na qual escutar por mensagens do grupo multicast.
  --disconnect_after DISCONNECT_AFTER
                        Número de falhas sequenciais necessárias para desconectar o Gateway.
  -l {DEBUG,INFO,WARN,ERROR}, --level {DEBUG,INFO,WARN,ERROR}
                        Nível do logging.
(venv) $ python semaphore.py
```

**Sensor de temperatura**

```bash
$ cd cidade_inteligente/devices/temp_sensor/
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ python temp_sensor.py --help
usage: temp_sensor.py [-h] [--id ID] [--multicast_ip MULTICAST_IP] [--multicast_port MULTICAST_PORT] [--report_interval REPORT_INTERVAL]
                      [--temperature TEMPERATURE] [--max_temperature MAX_TEMPERATURE] [--min_temperature MIN_TEMPERATURE]
                      [--disconnect_gateway_after DISCONNECT_GATEWAY_AFTER] [--disconnect_broker_after DISCONNECT_BROKER_AFTER]
                      [-l {DEBUG,INFO,WARN,ERROR}]

Sensor de temperatura.

options:
  -h, --help            show this help message and exit
  --id ID               Id que unicamente identifica o sensor de temperatura.
  --multicast_ip MULTICAST_IP
                        IP multicast para descobrimento do Gateway.
  --multicast_port MULTICAST_PORT
                        Porta na qual escutar por mensagens do grupo multicast.
  --report_interval REPORT_INTERVAL
                        Intervalo entre o envio de leituras.
  --temperature TEMPERATURE
                        Temperatura inicial do sensor em °C.
  --max_temperature MAX_TEMPERATURE
                        Temperatura máximo do sensor em °C.
  --min_temperature MIN_TEMPERATURE
                        Temperatura mínima do sensor em °C.
  --disconnect_gateway_after DISCONNECT_GATEWAY_AFTER
                        Número de falhas necessárias para desconectar o Gateway.
  --disconnect_broker_after DISCONNECT_BROKER_AFTER
                        Número de falhas necessárias para desconectar o Broker.
  -l {DEBUG,INFO,WARN,ERROR}, --level {DEBUG,INFO,WARN,ERROR}
                        Nível do logging.
(venv) $ python temp_sensor.py
```

**Cliente CLI**

```bash
$ cd cidade_inteligente/clients/simple_client/
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ python simple_client.py
>>> help
The following commands are available:
  help      : Show this help message
  sensors   : List sensors devices
  actuators : List actuators devices
  sensor <name>
            : Show all available data of sensor <name>
  actuator <name>
            : Show actuator <name> informations
  actuator <name> <action>
            : Send action <action> to actuator <name>
            : <name> and <action> must not be enclosed in double quotes
  actuator <name> <key> <value>
            : Set state <key> to <value> for actuator <name>
            : <value> must be a valid stringfyed JSON value
            : <key> must not be enclosed in double quotes
            : If <value> is a string, it must be enclosed in double quotes
```
