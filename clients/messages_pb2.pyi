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
DT_UNSPECIFIED: DeviceType
SENSOR: DeviceType
ACTUATOR: DeviceType

class Address(_message.Message):
    __slots__ = ("ip", "port")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ("type", "name", "state", "metadata")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    type: DeviceType
    name: str
    state: str
    metadata: str
    def __init__(self, type: _Optional[_Union[DeviceType, str]] = ..., name: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ...) -> None: ...

class JoinRequest(_message.Message):
    __slots__ = ("device_info", "device_address")
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    device_info: DeviceInfo
    device_address: Address
    def __init__(self, device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., device_address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class JoinReply(_message.Message):
    __slots__ = ("report_port", "report_interval")
    REPORT_PORT_FIELD_NUMBER: _ClassVar[int]
    REPORT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    report_port: int
    report_interval: float
    def __init__(self, report_port: _Optional[int] = ..., report_interval: _Optional[float] = ...) -> None: ...

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
    __slots__ = ("device_name", "action_value", "timestamp", "state", "metadata", "is_online")
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    ACTION_VALUE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    IS_ONLINE_FIELD_NUMBER: _ClassVar[int]
    device_name: str
    action_value: str
    timestamp: str
    state: str
    metadata: str
    is_online: bool
    def __init__(self, device_name: _Optional[str] = ..., action_value: _Optional[str] = ..., timestamp: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ..., is_online: bool = ...) -> None: ...

class ActuatorsReport(_message.Message):
    __slots__ = ("updates",)
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    updates: _containers.RepeatedCompositeFieldContainer[ActuatorUpdate]
    def __init__(self, updates: _Optional[_Iterable[_Union[ActuatorUpdate, _Mapping]]] = ...) -> None: ...
