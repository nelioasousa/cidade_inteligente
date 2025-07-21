# Cidade Inteligente - Cliente Flutter

Uma aplicação Flutter que implementa uma arquitetura MVVM para gerenciar sensores e atuadores de uma cidade inteligente.

## 📱 Arquitetura MVVM

A aplicação segue o padrão MVVM (Model-View-ViewModel) com as seguintes camadas:

### 📂 Estrutura de Pastas

```
lib/
├── models/              # Modelos de dados
│   ├── reading.dart     # Modelo para leituras de sensores
│   ├── sensor.dart      # Modelo para sensores
│   ├── actuator.dart    # Modelo para atuadores
│   └── api_response.dart # Modelo para respostas da API
├── services/            # Serviços de comunicação com a API
│   ├── sensor_service.dart    # Serviço para operações com sensores
│   └── actuator_service.dart  # Serviço para operações com atuadores
├── viewmodels/          # ViewModels (lógica de negócio e estado)
│   ├── sensor_viewmodel.dart    # ViewModel para sensores
│   └── actuator_viewmodel.dart  # ViewModel para atuadores
├── views/               # Telas da aplicação
│   ├── home_view.dart           # Tela principal com navegação
│   ├── sensor_list_view.dart    # Lista de sensores
│   ├── sensor_detail_view.dart  # Detalhes de um sensor
│   ├── actuator_list_view.dart  # Lista de atuadores
│   └── actuator_detail_view.dart # Detalhes de um atuador
└── main.dart            # Ponto de entrada da aplicação
```

### 🔧 Tecnologias Utilizadas

- **Flutter**: Framework para desenvolvimento mobile
- **Provider**: Gerenciamento de estado (implementação do padrão Observer)
- **HTTP**: Para comunicação com a API REST
- **Material Design**: Para interface do usuário

### 🌐 Endpoints da API

A aplicação consome os seguintes endpoints:

#### Sensores
- `GET /sensors` - Lista todos os sensores
- `GET /sensors/{category}/{id}` - Detalhes de um sensor específico

#### Atuadores
- `GET /actuators` - Lista todos os atuadores
- `GET /actuators/{category}/{id}` - Detalhes de um atuador específico
- `PUT /actuators/{category}/{id}` - Atualiza configurações de um atuador
- `POST /actuators/{category}/{id}` - Executa uma ação em um atuador

### 🏗️ Componentes da Arquitetura

#### Models
- **Reading**: Representa uma leitura de sensor (timestamp + valor)
- **Sensor**: Representa um sensor com suas propriedades e histórico
- **Actuator**: Representa um atuador com seu estado atual
- **ApiResponse**: Padroniza respostas da API

#### Services
- **SensorService**: Gerencia todas as operações relacionadas a sensores
- **ActuatorService**: Gerencia todas as operações relacionadas a atuadores

#### ViewModels
- **SensorViewModel**: Controla o estado e lógica relacionada aos sensores
- **ActuatorViewModel**: Controla o estado e lógica relacionada aos atuadores

#### Views
- **HomeView**: Navegação principal entre sensores e atuadores
- **SensorListView**: Exibe lista de sensores com status
- **SensorDetailView**: Mostra detalhes e histórico de um sensor
- **ActuatorListView**: Exibe lista de atuadores com status
- **ActuatorDetailView**: Permite controlar e configurar atuadores

### 🔄 Fluxo de Dados

1. **View** faz uma solicitação através do **ViewModel**
2. **ViewModel** chama o **Service** correspondente
3. **Service** faz a requisição HTTP para a API
4. **Service** converte a resposta JSON em **Models**
5. **ViewModel** atualiza seu estado interno
6. **View** é notificada automaticamente (via Provider) e se atualiza

### ⚙️ Configuração

1. Configure a URL base da API no arquivo `sensor_service.dart` e `actuator_service.dart`:
   ```dart
   static const String baseUrl = 'http://seu-servidor:porta';
   ```

2. Execute o projeto:
   ```bash
   flutter pub get
   flutter run
   ```

### 🎯 Funcionalidades

#### Sensores
- ✅ Visualizar lista de sensores
- ✅ Ver status online/offline
- ✅ Visualizar última leitura
- ✅ Ver histórico completo de leituras
- ✅ Atualizar dados via pull-to-refresh

#### Atuadores
- ✅ Visualizar lista de atuadores
- ✅ Ver status online/offline
- ✅ Visualizar estado atual
- ✅ Executar ações (ex: ligar/desligar lâmpada)
- ✅ **Mudar cor das lâmpadas** (via PUT com parâmetro Color)
- ✅ **Cores disponíveis**: white (branco) e yellow (amarelo)
- ✅ **Controle de brilho das lâmpadas** (via PUT com parâmetro Brightness)
- ✅ **Brilho**: valores de 1 a 10 com slider e campo numérico
- ✅ **Chips de cores e brilho** para seleção rápida
- ✅ **Validação** para cores e brilho permitidos
- ✅ Configurar parâmetros (ex: tempos do semáforo)
- ✅ Feedback de sucesso/erro nas operações

### 📱 Interface do Usuário

- **Design Material 3**: Interface moderna e responsiva
- **Navegação por Tabs**: Acesso rápido entre sensores e atuadores
- **Cards Informativos**: Apresentação clara dos dados
- **Estados de Loading**: Indicadores visuais durante operações
- **Tratamento de Erros**: Mensagens claras e opções de retry
- **Pull-to-Refresh**: Atualização manual dos dados

### 🔧 Extensibilidade

A arquitetura permite fácil extensão para:
- Novos tipos de sensores e atuadores
- Novos endpoints da API
- Novas funcionalidades de interface
- Diferentes fontes de dados
- Notificações e alertas
- Gráficos e visualizações avançadas


