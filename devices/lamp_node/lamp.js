const CONTROLLER_MULTICAST = require('./controllerGatewayTCP');
const CONTROLLER_GATEWAY = require('./controllerMulticastUDP');


/**
 * Iniciar atuador
 */
console.log('INICIANDO ATUADOR');
CONTROLLER_MULTICAST.createSocketMulticast();
CONTROLLER_MULTICAST.connectToMulticast();

/**
 * Metodo para encerrar o atuador
 */
process.on('SIGINT', () => {
  console.log('Desligando atuador...');
  
  if (CONTROLLER_MULTICAST.socket != null) {
    CONTROLLER_MULTICAST.socket.close(() => {
    process.exit(0);
  });
  }
  
  if(CONTROLLER_GATEWAY.server != null) {
    CONTROLLER_GATEWAY.server.close(() => {
    process.exit(0);
  });
  }  
});

