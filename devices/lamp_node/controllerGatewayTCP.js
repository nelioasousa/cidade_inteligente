const net = require('net');
const protobuf = require("protobufjs");
const { ActuatorUpdate, JoinRequest, JoinReply, DeviceType, DeviceInfo, Address } = require('./protos/messages_pb');

/**
 * Informaçoes do Cliente <> Gateway
 */

let IS_ONLINE = false;

/**
 * Informaçoes do atuador
 */
const DEVICE_NAME = "LAMP";
let LAMP_STATE = '{"isOn": "sim", "Color": "yellow", "Brightness": 10}';
const LAMP_METADATA = '{"isOn": "(sim ou nao)", "Color": "(yellow ou branco)", "Brightness": "(Entre 1 a 10)"}';
const PORT_ATUADOR = 60555;
const HOST_ATUADOR = '127.0.0.1';

/**
 * Variavel servidor TCP
 */
let server = null;
let connectionGateway = null;

function connectToGateway(ipGateway, portGateway) {

    portGatewayToConnect = portGateway;

    // Criando conexao TCP com Gateway
    connectionGateway = net.createConnection({
        host: ipGateway,
        port: portGatewayToConnect
    }, () => {
        console.log(`Conectado ao gateway ${ipGateway}:${portGatewayToConnect}`);
    });

    // JoinRequest para o Gateway
    const dataRegisterActuator = new DeviceInfo();
    dataRegisterActuator.setDeviceType(DeviceType.DT_ACTUATOR);
    dataRegisterActuator.setName(DEVICE_NAME);
    dataRegisterActuator.setState(LAMP_STATE.STATE);
    dataRegisterActuator.setMetadata(LAMP_METADATA);
    dataRegisterActuator.setTimestamp(new Date(Date.now()).toString());

    const address = new Address();
    address.setIp(HOST_ATUADOR);
    address.setPort(PORT_ATUADOR);

    const joinRequest = new JoinRequest();
    joinRequest.setDeviceInfo(dataRegisterActuator);
    joinRequest.setDeviceAddress(address);

    const msgSend = joinRequest.serializeBinary();
    connectionGateway.write(msgSend); 

    // JoinReplay do Gateway
    connectionGateway.on('data', (data) => {
        const joinReplay = JoinReply.deserializeBinary(data);
        portGatewayToConnect = joinReplay.report_port;
    });

    connectionGateway.end();

    // Criando uma nova conexao TCP com o Gateway em outra porta
    connectionGateway = net.createConnection({
        host: ipGateway,
        port: portGatewayToConnect
    }, () => {
        console.log(`Conectado ao gateway ${ipGateway}:${portGatewayToConnect}`);
    });

    // Recebendo comandos do Gateway
    connectionGateway.on('data', (data) => {
        const actuatorUpdate = ActuatorUpdate.deserializeBinary(data);

        LAMP_STATE.STATE = actuatorUpdate.state;
        IS_ONLINE = actuatorUpdate.is_online;

        //colocar dentro do cliente <> gateway
        const dataResp = new ActuatorUpdate();
        dataResp.setDeviceName(DEVICE_NAME);
        dataResp.setState(LAMP_STATE.STATE);
        dataResp.setMetadata(LAMP_METADATA);
        dataResp.setTimestamp(new Date(Date.now()).toString());
        dataResp.setIsOnline(IS_ONLINE);

        const msgResponse = dataResp.serializeBinary();

        // Envia a mensagem para gateway
        connectionGateway.write(msgResponse);

    });

    startServer();
}

function startServer() {
    // Cria o servidor TCP
    server = net.createServer((socket) => {

        // Receber comandos
        socket.on('data', (data) => {
            
            const actuatorUpdate = ActuatorUpdate.deserializeBinary(data);

            LAMP_STATE.STATE = actuatorUpdate.state;
            IS_ONLINE = actuatorUpdate.is_online;
            
            //colocar dentro do cliente <> gateway
            const dataResp = new ActuatorUpdate();
            dataResp.setDeviceName(DEVICE_NAME);
            dataResp.setState(LAMP_STATE.STATE);
            dataResp.setMetadata(LAMP_METADATA);
            dataResp.setTimestamp(new Date(Date.now()).toString());
            dataResp.setIsOnline(IS_ONLINE);

            const msgResponse = dataResp.serializeBinary();
  
            // Envia a mensagem para gateway
            connectionGateway.write(msgResponse);
        });

        // Evento: cliente desconectado
        socket.on('end', () => {
            console.log('Gateway desconectado');
        });

        // Evento: erro na conexão
        socket.on('error', (err) => {
            console.error('Erro no socket:', err.message);
        });

    });

    // Inicia o servidor
    server.listen(PORT_ATUADOR, HOST_ATUADOR, () => {
        console.log(`Atuador rodando em ${HOST}:${PORT}`);
    });

    // Tratamento de erros gerais do servidor
    server.on('error', (err) => {
        console.error('Erro no atuador:', err.message);
    });
}

function closeConnectionAtuador() {
    if(server != null) {
        server.close();
    }

    if(connectionGateway != null) {
        connectionGateway.end();
    }
}

module.exports = {
  server,
  connectToGateway,
  closeConnectionAtuador
};