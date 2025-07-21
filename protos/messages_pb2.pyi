from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

CS_FAIL: ComplyStatus
CS_INVALID_STATE: ComplyStatus
CS_OK: ComplyStatus
CS_UNKNOWN_ACTION: ComplyStatus
CS_UNSPECIFIED: ComplyStatus
CT_ACTION: CommandType
CT_GET_STATE: CommandType
CT_SET_STATE: CommandType
CT_UNSPECIFIED: CommandType
DESCRIPTOR: _descriptor.FileDescriptor
DT_ACTUATOR: DeviceType
DT_SENSOR: DeviceType
DT_UNSPECIFIED: DeviceType
RS_FAIL: ReplyStatus
RS_INVALID_STATE: ReplyStatus
RS_OK: ReplyStatus
RS_UNKNOWN_ACTION: ReplyStatus

class Address(_message.Message):
    __slots__ = ("ip", "port", "broker_ip", "broker_port", "publish_exchange")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    BROKER_IP_FIELD_NUMBER: _ClassVar[int]
    BROKER_PORT_FIELD_NUMBER: _ClassVar[int]
    PUBLISH_EXCHANGE_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    broker_ip: str
    broker_port: int
    publish_exchange: str
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ..., broker_ip: _Optional[str] = ..., broker_port: _Optional[int] = ..., publish_exchange: _Optional[str] = ...) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ("type", "name", "state", "metadata", "timestamp")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    type: DeviceType
    name: str
    state: str
    metadata: str
    timestamp: str
    def __init__(self, type: _Optional[_Union[DeviceType, str]] = ..., name: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class JoinRequest(_message.Message):
    __slots__ = ("device_info", "device_address")
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    device_info: DeviceInfo
    device_address: Address
    def __init__(self, device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., device_address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class JoinReply(_message.Message):
    __slots__ = ("report_port",)
    REPORT_PORT_FIELD_NUMBER: _ClassVar[int]
    report_port: int
    def __init__(self, report_port: _Optional[int] = ...) -> None: ...

class SensorReading(_message.Message):
    __slots__ = ("device_name", "reading_value", "metadata", "timestamp", "is_online")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    READING_VALUE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    reading_value: float
    metadata: str
    timestamp: str
    is_online: bool
    def __init__(self, device_name: _Optional[str] = ..., reading_value: _Optional[float] = ..., metadata: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_online: bool = ...) -> None: ...

class ActuatorUpdate(_message.Message):
    __slots__ = ("device_name", "state", "metadata", "timestamp", "is_online")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    state: str
    metadata: str
    timestamp: str
    is_online: bool
    def __init__(self, device_name: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_online: bool = ...) -> None: ...

class ActuatorCommand(_message.Message):
    __slots__ = ["body", "type"]
    BODY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    body: str
    type: CommandType
    def __init__(self, type: _Optional[_Union[CommandType, str]] = ..., body: _Optional[str] = ...) -> None: ...

class ActuatorComply(_message.Message):
    __slots__ = ["status", "update"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    status: ComplyStatus
    update: ActuatorUpdate
    def __init__(self, status: _Optional[_Union[ComplyStatus, str]] = ..., update: _Optional[_Union[ActuatorUpdate, _Mapping]] = ...) -> None: ...

class ActuatorUpdate(_message.Message):
    __slots__ = ["device_name", "is_online", "metadata", "state", "timestamp"]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    is_online: bool
    metadata: str
    state: str
    timestamp: str
    def __init__(self, device_name: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_online: bool = ...) -> None: ...

class ActuatorsReport(_message.Message):
    __slots__ = ["devices"]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[ActuatorUpdate]
    def __init__(self, devices: _Optional[_Iterable[_Union[ActuatorUpdate, _Mapping]]] = ...) -> None: ...

class Address(_message.Message):
    __slots__ = ["ip", "port"]
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class ClientReply(_message.Message):
    __slots__ = ["data", "reply_to", "status"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    REPLY_TO_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    reply_to: RequestType
    status: ReplyStatus
    def __init__(self, status: _Optional[_Union[ReplyStatus, str]] = ..., reply_to: _Optional[_Union[RequestType, str]] = ..., data: _Optional[bytes] = ...) -> None: ...

class ClientRequest(_message.Message):
    __slots__ = ["body", "device_name", "type"]
    BODY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    body: str
    device_name: str
    type: RequestType
    def __init__(self, type: _Optional[_Union[RequestType, str]] = ..., device_name: _Optional[str] = ..., body: _Optional[str] = ...) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ["metadata", "name", "state", "timestamp", "type"]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    metadata: str
    name: str
    state: str
    timestamp: str
    type: DeviceType
    def __init__(self, type: _Optional[_Union[DeviceType, str]] = ..., name: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class JoinReply(_message.Message):
    __slots__ = ["report_port"]
    REPORT_PORT_FIELD_NUMBER: _ClassVar[int]
    report_port: int
    def __init__(self, report_port: _Optional[int] = ...) -> None: ...

class JoinRequest(_message.Message):
    __slots__ = ["device_address", "device_info"]
    DEVICE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    device_address: Address
    device_info: DeviceInfo
    def __init__(self, device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., device_address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class SensorData(_message.Message):
    __slots__ = ["device_name", "is_online", "metadata", "readings"]
    class SimpleReading(_message.Message):
        __slots__ = ["reading_value", "timestamp"]
        READING_VALUE_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        reading_value: float
        timestamp: str
        def __init__(self, timestamp: _Optional[str] = ..., reading_value: _Optional[float] = ...) -> None: ...
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    READINGS_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    is_online: bool
    metadata: str
    readings: _containers.RepeatedCompositeFieldContainer[SensorData.SimpleReading]
    def __init__(self, device_name: _Optional[str] = ..., metadata: _Optional[str] = ..., readings: _Optional[_Iterable[_Union[SensorData.SimpleReading, _Mapping]]] = ..., is_online: bool = ...) -> None: ...

class SensorReading(_message.Message):
    __slots__ = ["device_name", "is_online", "metadata", "reading_value", "timestamp"]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    READING_VALUE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    is_online: bool
    metadata: str
    reading_value: float
    timestamp: str
    def __init__(self, device_name: _Optional[str] = ..., reading_value: _Optional[float] = ..., metadata: _Optional[str] = ..., timestamp: _Optional[str] = ..., is_online: bool = ...) -> None: ...

class SensorsReport(_message.Message):
    __slots__ = ["devices"]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[SensorReading]
    def __init__(self, devices: _Optional[_Iterable[_Union[SensorReading, _Mapping]]] = ...) -> None: ...

class DeviceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class CommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ComplyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ReplyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
