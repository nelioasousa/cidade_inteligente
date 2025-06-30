const net = require('net');
const protobuf = require("protobufjs");
const { ActuatorUpdate, JoinRequest, JoinReply, DeviceType, DeviceInfo, Address, ActuatorCommand, ActuatorComply, CommandType, ComplyStatus} = require('./protos/messages_pb');


/**
 * Informaçoes do atuador
 */
const DEVICE_NAME = "LAMP";
let LAMP_STATE = '{"isOn": "yes" ,"Color": "yellow", "Brightness": 10}';
const LAMP_METADATA = '{"isOn": "(yes ou no)", "Color": "(yellow ou white)", "Brightness": "(Between 1 and 10)", "Actions": ["turn_on", "turn_off"]}';
const PORT_ATUADOR = 60555;
const HOST_ATUADOR = '127.0.0.1';

/**
 * Variavel servidor TCP
 */
let server = null;
let connectionGateway = null;
let portTrasferData = null;
let hostTrasferData = null;

function connectToGateway(ipGateway, portGateway) {

    if (connectionGateway != null) return;

    portGatewayToConnect = portGateway;
    hostTrasferData = ipGateway;

    // Criando conexao TCP com Gateway
    connectionGateway = net.createConnection({
        host: ipGateway,
        port: portGatewayToConnect
    }, () => {
        console.log(`Conectado ao gateway ${ipGateway}:${portGatewayToConnect}`);
    });

    // JoinRequest para o Gateway
    const dataRegisterActuator = new DeviceInfo();
    dataRegisterActuator.setType(DeviceType.DT_ACTUATOR);
    dataRegisterActuator.setName(DEVICE_NAME);
    dataRegisterActuator.setState(LAMP_STATE);
    dataRegisterActuator.setMetadata(LAMP_METADATA);
    dataRegisterActuator.setTimestamp(new Date(Date.now()).toISOString());

    const address = new Address(); // porta do atuador 
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
        portTrasferData = joinReplay.getReportPort(); // porta do gateway que o atuador deve usar
        console.log(`Porta do gateway para transferencia de dados: ${portTrasferData}`);
        connectPortTrasferData();
    });
}

function connectPortTrasferData() {
    closeConnectionGateway();
    // Criando uma nova conexao TCP com o Gateway em outra porta
    connectionGateway = net.createConnection({
        host: hostTrasferData,
        port: portTrasferData,
    }, () => {
        console.log(`Conectado ao gateway ${hostTrasferData}:${portTrasferData}`);
    });
    // criando servidor atuador porta 60555
    startServer();
}

function startServer() {
    // Cria o servidor TCP
    server = net.createServer((socket) => {

        // Receber comandos
        socket.on('data', (data) => {
            
            // ActuatorCommand -> recebe
            const actuatorCommand = ActuatorCommand.deserializeBinary(data);

            if (actuatorCommand == CommandType.CT_GET_STATE) {
                sendDataGateway(ComplyStatus.CS_OK);
            } else if (actuatorCommand == CommandType.CT_ACTION) {
                if (actuatorCommand.getBody().toLowerCase() == "turn_on") {
                    const jsonState = JSON.parse(LAMP_STATE);
                    jsonState.isOn = "yes";
                    LAMP_STATE = JSON.stringify(jsonState);
                    sendDataGateway(ComplyStatus.CS_OK);
                }
                else if (actuatorCommand.getBody().toLowerCase() == "turn_off") {
                    const jsonState = JSON.parse(LAMP_STATE);
                    jsonState.isOn = "no";
                    LAMP_STATE = JSON.stringify(jsonState);
                    sendDataGateway(ComplyStatus.CS_OK);
                }
                else {
                    sendDataGateway(ComplyStatus.CS_UNKNOWN_ACTION);
                }
            }
            else if (actuatorCommand == CommandType.CT_SET_STATE) {
                if (validarBody()) {
                    LAMP_STATE = actuatorCommand.getBody();
                    sendDataGateway(ComplyStatus.CS_OK);
                }
                else {
                    sendDataGateway(ComplyStatus.CS_INVALID_STATE);
                }
                
            }
            else if (actuatorCommand == CommandType.CT_UNSPECIFIED) {
                sendDataGateway(ComplyStatus.CS_UNSPECIFIED);
            }
        });

        // Evento: cliente desconectado
        socket.on('end', () => {
            sendDataGateway(ComplyStatus.CS_FAIL);
            console.log('Atuador desconectado');
        });

        // Evento: erro na conexão
        socket.on('error', (err) => {
            sendDataGateway(ComplyStatus.CS_FAIL);
            console.error('Erro no atuador:', err.message);
        });

    });

    // Inicia o servidor
    server.listen(PORT_ATUADOR, HOST_ATUADOR, () => {
        console.log(`Atuador rodando em ${HOST_ATUADOR}:${PORT_ATUADOR}`);
    });

    // Tratamento de erros gerais do servidor
    server.on('error', (err) => {
        sendDataGateway(ComplyStatus.CS_FAIL);
        console.error('Erro no atuador:', err.message);
    });
}

function sendDataGateway(complyStatus) {

    if (connectionGateway != null) {
        // Envia dados para o gateway
        const actuatorUpdate = new ActuatorUpdate();
        actuatorUpdate.setDeviceName(DEVICE_NAME);
        actuatorUpdate.setState(LAMP_STATE);
        actuatorUpdate.setMetadata(LAMP_METADATA);
        actuatorUpdate.setTimestamp(new Date(Date.now()).toISOString());
        //actuatorUpdate.setIsOnline(false);

        // ActuatorComply -> manda uma mensagem o gateway
        const actuatorComply = new ActuatorComply();
        actuatorComply.setStatus(complyStatus);
        actuatorComply.setUpdate(actuatorUpdate);

        const msgResponse = actuatorComply.serializeBinary();

        // Envia a mensagem para gateway
        connectionGateway.write(msgResponse);
    }
}

function turnOffAtuador() {
    if(server != null) {
        server.close();
    }
}

function closeConnectionGateway() {
    if(connectionGateway != null) {
        connectionGateway.end();
        connectionGateway = null;
    }
}

module.exports = {
  server,
  connectToGateway,
  turnOffAtuador,
  closeConnectionGateway
};