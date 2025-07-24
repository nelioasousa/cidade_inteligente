# 🌐 Cidade Inteligente - Sistemas Distribuídos com Sockets
Este projeto simula uma Cidade Inteligente com sensores e atuadores que se comunicam com um Gateway central. Foi desenvolvido um cliente CLI que permite o monitoramento e controle dos dispositivos inteligentes.


## 🧠 O que é?

Um sistema distribuído para aprendizado de comunicação entre processos. Ele simula:

- **Dispositivos Inteligentes:** sensores e atuadores que interagem com o ambiente.
- **Gateway Central:** responsável pela coordenação e comunicação entre dispositivos.
- **Cliente CLI:** interface de controle e monitoramento em tempo real.

## 🔧 Tecnologias Utilizadas

- **Ubuntu-24.04:** os sockets foram configurados tendo em mente uma plataforma Unix;
- **Python v3.12.3:** desenvolvimento do gateway, cliente CLI, sensor de temperatura e semáforo (atuador);
- **Node.js v20.18.2:** poste de iluminação (lâmpada inteligente);
- **Sockets TCP e UDP:** comunicação entre dispositivos;
- **UDP Multicast:** dispositivos inteligêntes descobrem a localização do gateway usando um grupo multicast;
- **libprotoc v31.1:** compilação das mensagens `.proto`.

## 📦 Estrutura de Diretórios

```
cidade_inteligente/
├── clients/
│   └── simple_client/      # Cliente CLI Python
├── devices/                # Código dos dispositivos inteligentes
│   ├── lamp_node/          # Lâmpada inteligente em Node.js
│   ├── semaphore/          # Semáforo em Python
│   └── temp_sensor/        # Sensor de temperatura em Python
├── exemplos/               # Code snippets
├── gateway/                # Código do Gateway em Python
│   ├── gateway.py               # Entry-point do Gateway
|   ├── db.py                    # Abstração de um banco de dados
|   ├── registration_handler.py  # Módulo responsável pelo multicast e registro de dispostivos
|   ├── sensors_handler.py       # Módulo responsável pelos sensores
|   ├── actuators_handler.py     # Módulo responsável pelos atuadores
|   └── clients_handler.py       # Módulo responsável pelos clientes
├── protos/                 
│   └── messages.proto       # Mensagens do Protobuf
├── python-requirements.txt  # Lista de dependência Python
└── README.md                # Documentação principal
```

## Diagramas de funcionamento
```mermaid
flowchart BT
    subgraph Gateway
        descobrimento([Serviço de Descobrimento])
        registro([Serviço de Registro])
        sensores([Serviço de Sensores])
        atuadores([Serviço de Atuadores])
        relatorios([Gerador de Relatórios])
    end

    desc_descobrimento[Socket UDP enviando o endereço do Serviço de Registro ao grupo multicast 224.0.1.0 na porta 50333. Envia a cada 5 segundos.]
    desc_descobrimento --- descobrimento

    desc_registro[Servidor TCP escutando na porta 50111. É responsável pelo registro de dispositivos inteligentes.]
    desc_registro --- registro

    desc_sensores[Socket UDP escutando na porta 50222. É responsável por receber leituras dos sensores registrados.]
    desc_sensores --- sensores

    desc_atuadores[Servidor TCP escutando na porta 50222. É responsável por receber atualizações dos atuadores registrados. Também possuí funcionalidades para enviar comandos aos atuadores.]
    desc_atuadores --- atuadores

    desc_relatorios[Gera a cada 5 segundos relatórios sobre os dispositivos registrados. Os relatórios contêm informações como metadados, estado e disponibilidade. Os clientes podem solicitar os relatórios.]
    desc_relatorios --- relatorios
```

```mermaid
flowchart TD
    subgraph Sensor
        envio([Thread de envio de dados])
        descobrimento([Thread de descobrimento e checagem de disponibilidade])
    end

    enviar[Enviar leitura]
    esperar[Esperar conexão]
    conectar[Se registrar no Gateway]
    desconectar[Desconectar dispositivo e realizar novo registro]
    desconectar_se[Desconectar se conectado]
    continuar[Continuar escutando]
    continuar_conn[Continuar conectado]

    perg_conn{Conectado ao Gateway?}
    perg_escutou{Escutou o endereço do Gateway no grupo multicast?}
    perg_realocar{O IP recebido no multicast mudou?}
    perg_falhas{3 falhas seguidas ao tentar receber endereço?}

    descobrimento-->perg_escutou
    perg_escutou-->|Não|perg_falhas
    perg_escutou-->|Sim|perg_conn
    perg_falhas-->|Sim|desconectar_se
    desconectar_se-->continuar
    perg_falhas-->|Não|continuar
    perg_conn-->|Não|conectar
    conectar-->continuar
    perg_conn-->|Sim|perg_realocar
    perg_realocar-->|Não|continuar_conn
    continuar_conn-->continuar
    perg_realocar-->|Sim|desconectar
    desconectar-->continuar

    envio-->envp1
    envp1{Conectado ao Gateway?}
    envp1-->|Sim|enviar
    envp1-->|Não|esperar
```

```mermaid
flowchart TD
    subgraph Atuador
        envio([Thread de envio de dados])
        descobrimento([Thread de descobrimento e checagem de disponibilidade])
        comandos([Servidor TCP esperando comandos do Gateway])
    end

    conectar[Se registrar no Gateway]
    desconectar[Desconectar dispositivo e realizar novo registro]
    desconectar_se[Desconectar se conectado]
    continuar[Continuar escutando]
    continuar_conn[Continuar conectado]

    perg_conn{Conectado ao Gateway?}
    perg_escutou{Escutou o endereço do Gateway no grupo multicast?}
    perg_realocar{O IP recebido no multicast mudou?}
    perg_falhas{3 falhas seguidas ao tentar receber endereço?}

    descobrimento-->perg_escutou
    perg_escutou-->|Não|perg_falhas
    perg_escutou-->|Sim|perg_conn
    perg_falhas-->|Sim|desconectar_se
    desconectar_se-->continuar
    perg_falhas-->|Não|continuar
    perg_conn-->|Não|conectar
    conectar-->continuar
    perg_conn-->|Sim|perg_realocar
    perg_realocar-->|Não|continuar_conn
    continuar_conn-->continuar
    perg_realocar-->|Sim|desconectar
    desconectar-->continuar

    enviar[Enviar atualização ao Gateway]
    esperar[Esperar conexão]

    perg_atualizacao{Atualização de estado?}
    perg_conn_envio{Conectado ao Gateway?}
    perg_passou{Passou 5 segundos sem novas atualizações?}

    envio-->perg_conn_envio
    perg_conn_envio-->|Sim|perg_atualizacao
    perg_conn_envio-->|Não|esperar
    perg_atualizacao-->|Não|perg_passou
    perg_atualizacao-->|Sim|enviar
    perg_passou-->|Sim|enviar
```

## ▶️ Como Executar

### 1. Compilar o arquivo de mensagens

```bash
$ cd protos/
$ protoc --version
libprotoc 31.1
# Python
$ protoc --python_out=. --pyi_out=. messages.proto
# Node.js
$ protoc --js_out=import_style=commonjs,binary:. messages.proto
```

### 2. Rodar os processos

**Python:**
```bash
$ cd cidade_inteligente/
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r python-requirements.txt
(venv) $ python gateway/gateway.py --help
```
ou
```bash
(venv) $ python devices/semaphore/semaphore.py --help
```
ou
```bash
(venv) $ python devices/temp_sensor/temp_sensor.py --help
```
ou
```bash
(venv) $ python clients/simple_client/simple_client.py
>>> help
```

**Node.js:**
```bash
$ cd cidade_inteligente/
$ npm install protobufjs
$ node devices/lamp_node/lamp.js
```
