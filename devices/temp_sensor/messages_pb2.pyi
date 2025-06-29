from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DT_UNSPECIFIED: _ClassVar[DeviceType]
    DT_SENSOR: _ClassVar[DeviceType]
    DT_ACTUATOR: _ClassVar[DeviceType]

class CommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CT_UNSPECIFIED: _ClassVar[CommandType]
    CT_ACTION: _ClassVar[CommandType]
    CT_GET_STATE: _ClassVar[CommandType]
    CT_SET_STATE: _ClassVar[CommandType]

class ComplyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CS_UNSPECIFIED: _ClassVar[ComplyStatus]
    CS_OK: _ClassVar[ComplyStatus]
    CS_FAIL: _ClassVar[ComplyStatus]
    CS_UNKNOWN_ACTION: _ClassVar[ComplyStatus]
    CS_INVALID_STATE: _ClassVar[ComplyStatus]

class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RT_UNSPECIFIED: _ClassVar[RequestType]
    RT_GET_SENSOR_DATA: _ClassVar[RequestType]
    RT_GET_ACTUATOR_UPDATE: _ClassVar[RequestType]
    RT_SET_ACTUATOR_STATE: _ClassVar[RequestType]
    RT_RUN_ACTUATOR_ACTION: _ClassVar[RequestType]

class ReplyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RS_UNSPECIFIED: _ClassVar[ReplyStatus]
    RS_OK: _ClassVar[ReplyStatus]
    RS_FAIL: _ClassVar[ReplyStatus]
    RS_INVALID_STATE: _ClassVar[ReplyStatus]
    RS_UNKNOWN_DEVICE: _ClassVar[ReplyStatus]
    RS_UNKNOWN_ACTION: _ClassVar[ReplyStatus]
DT_UNSPECIFIED: DeviceType
DT_SENSOR: DeviceType
DT_ACTUATOR: DeviceType
CT_UNSPECIFIED: CommandType
CT_ACTION: CommandType
CT_GET_STATE: CommandType
CT_SET_STATE: CommandType
CS_UNSPECIFIED: ComplyStatus
CS_OK: ComplyStatus
CS_FAIL: ComplyStatus
CS_UNKNOWN_ACTION: ComplyStatus
CS_INVALID_STATE: ComplyStatus
RT_UNSPECIFIED: RequestType
RT_GET_SENSOR_DATA: RequestType
RT_GET_ACTUATOR_UPDATE: RequestType
RT_SET_ACTUATOR_STATE: RequestType
RT_RUN_ACTUATOR_ACTION: RequestType
RS_UNSPECIFIED: ReplyStatus
RS_OK: ReplyStatus
RS_FAIL: ReplyStatus
RS_INVALID_STATE: ReplyStatus
RS_UNKNOWN_DEVICE: ReplyStatus
RS_UNKNOWN_ACTION: ReplyStatus

class Address(_message.Message):
    __slots__ = ("ip", "port")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

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
    __slots__ = ("type", "body")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    type: CommandType
    body: str
    def __init__(self, type: _Optional[_Union[CommandType, str]] = ..., body: _Optional[str] = ...) -> None: ...

class ActuatorComply(_message.Message):
    __slots__ = ("status", "update")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    status: ComplyStatus
    update: ActuatorUpdate
    def __init__(self, status: _Optional[_Union[ComplyStatus, str]] = ..., update: _Optional[_Union[ActuatorUpdate, _Mapping]] = ...) -> None: ...

class SensorData(_message.Message):
    __slots__ = ("device_name", "metadata", "readings", "is_online")
    class SimpleReading(_message.Message):
        __slots__ = ("timestamp", "reading_value")
        TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        READING_VALUE_FIELD_NUMBER: _ClassVar[int]
        timestamp: str
        reading_value: float
        def __init__(self, timestamp: _Optional[str] = ..., reading_value: _Optional[float] = ...) -> None: ...
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    READINGS_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    metadata: str
    readings: _containers.RepeatedCompositeFieldContainer[SensorData.SimpleReading]
    is_online: bool
    def __init__(self, device_name: _Optional[str] = ..., metadata: _Optional[str] = ..., readings: _Optional[_Iterable[_Union[SensorData.SimpleReading, _Mapping]]] = ..., is_online: bool = ...) -> None: ...

class SensorsReport(_message.Message):
    __slots__ = ("devices",)
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[SensorReading]
    def __init__(self, devices: _Optional[_Iterable[_Union[SensorReading, _Mapping]]] = ...) -> None: ...

class ActuatorsReport(_message.Message):
    __slots__ = ("devices",)
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[ActuatorUpdate]
    def __init__(self, devices: _Optional[_Iterable[_Union[ActuatorUpdate, _Mapping]]] = ...) -> None: ...

class SendNextReport(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConnectionRequest(_message.Message):
    __slots__ = ("sensors_port", "actuators_port")
    SENSORS_PORT_FIELD_NUMBER: _ClassVar[int]
    ACTUATORS_PORT_FIELD_NUMBER: _ClassVar[int]
    sensors_port: int
    actuators_port: int
    def __init__(self, sensors_port: _Optional[int] = ..., actuators_port: _Optional[int] = ...) -> None: ...

class ClientRequest(_message.Message):
    __slots__ = ("type", "device_name", "body")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    type: RequestType
    device_name: str
    body: str
    def __init__(self, type: _Optional[_Union[RequestType, str]] = ..., device_name: _Optional[str] = ..., body: _Optional[str] = ...) -> None: ...

class ClientReply(_message.Message):
    __slots__ = ("status", "reply_to", "data")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    REPLY_TO_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    status: ReplyStatus
    reply_to: RequestType
    data: bytes
    def __init__(self, status: _Optional[_Union[ReplyStatus, str]] = ..., reply_to: _Optional[_Union[RequestType, str]] = ..., data: _Optional[bytes] = ...) -> None: ...
