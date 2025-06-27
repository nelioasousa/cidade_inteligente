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
    SENSOR: _ClassVar[DeviceType]
    ACTUATOR: _ClassVar[DeviceType]

class CommandType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CT_UNSPECIFIED: _ClassVar[CommandType]
    ACTION: _ClassVar[CommandType]
    GET_STATE: _ClassVar[CommandType]
    SET_STATE: _ClassVar[CommandType]

class ComplyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CS_UNSPECIFIED: _ClassVar[ComplyStatus]
    OK: _ClassVar[ComplyStatus]
    FAIL: _ClassVar[ComplyStatus]
    UNKNOWN_ACTION: _ClassVar[ComplyStatus]
DT_UNSPECIFIED: DeviceType
SENSOR: DeviceType
ACTUATOR: DeviceType
CT_UNSPECIFIED: CommandType
ACTION: CommandType
GET_STATE: CommandType
SET_STATE: CommandType
CS_UNSPECIFIED: ComplyStatus
OK: ComplyStatus
FAIL: ComplyStatus
UNKNOWN_ACTION: ComplyStatus

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
    __slots__ = ("device_name", "reading_value", "timestamp", "metadata", "is_online")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    READING_VALUE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    reading_value: str
    timestamp: str
    metadata: str
    is_online: bool
    def __init__(self, device_name: _Optional[str] = ..., reading_value: _Optional[str] = ..., timestamp: _Optional[str] = ..., metadata: _Optional[str] = ..., is_online: bool = ...) -> None: ...

class SensorsReport(_message.Message):
    __slots__ = ("readings",)
    READINGS_FIELD_NUMBER: _ClassVar[int]
    readings: _containers.RepeatedCompositeFieldContainer[SensorReading]
    def __init__(self, readings: _Optional[_Iterable[_Union[SensorReading, _Mapping]]] = ...) -> None: ...

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

class ActuatorsReport(_message.Message):
    __slots__ = ("updates",)
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    updates: _containers.RepeatedCompositeFieldContainer[ActuatorUpdate]
    def __init__(self, updates: _Optional[_Iterable[_Union[ActuatorUpdate, _Mapping]]] = ...) -> None: ...

class ActuatorCommand(_message.Message):
    __slots__ = ("type", "body")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    type: CommandType
    body: str
    def __init__(self, type: _Optional[_Union[CommandType, str]] = ..., body: _Optional[str] = ...) -> None: ...

class ActuatorComply(_message.Message):
    __slots__ = ("status", "body")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    status: ComplyStatus
    body: str
    def __init__(self, status: _Optional[_Union[ComplyStatus, str]] = ..., body: _Optional[str] = ...) -> None: ...
