from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RT_UNSPECIFIED: _ClassVar[RequestType]
    ACTION: _ClassVar[RequestType]
    GET_STATE: _ClassVar[RequestType]
    SET_STATE: _ClassVar[RequestType]

class ReplyStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RS_UNSPECIFIED: _ClassVar[ReplyStatus]
    OK: _ClassVar[ReplyStatus]
    BAD_REQUEST: _ClassVar[ReplyStatus]
    FAIL: _ClassVar[ReplyStatus]
    DENIED: _ClassVar[ReplyStatus]
    TIMEOUT: _ClassVar[ReplyStatus]
    UNKNOWN_TYPE: _ClassVar[ReplyStatus]
    UNKNOWN_ACTION: _ClassVar[ReplyStatus]
RT_UNSPECIFIED: RequestType
ACTION: RequestType
GET_STATE: RequestType
SET_STATE: RequestType
RS_UNSPECIFIED: ReplyStatus
OK: ReplyStatus
BAD_REQUEST: ReplyStatus
FAIL: ReplyStatus
DENIED: ReplyStatus
TIMEOUT: ReplyStatus
UNKNOWN_TYPE: ReplyStatus
UNKNOWN_ACTION: ReplyStatus

class Address(_message.Message):
    __slots__ = ("ip", "port")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ("name", "state")
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    name: str
    state: str
    def __init__(self, name: _Optional[str] = ..., state: _Optional[str] = ...) -> None: ...

class JoinRequest(_message.Message):
    __slots__ = ("device_info", "device_address")
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    device_info: DeviceInfo
    device_address: Address
    def __init__(self, device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., device_address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class JoinReply(_message.Message):
    __slots__ = ("report_address", "report_interval")
    REPORT_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    REPORT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    report_address: Address
    report_interval: float
    def __init__(self, report_address: _Optional[_Union[Address, _Mapping]] = ..., report_interval: _Optional[float] = ...) -> None: ...

class SensorReading(_message.Message):
    __slots__ = ("sensor_name", "reading_value", "timestamp")
    SENSOR_NAME_FIELD_NUMBER: _ClassVar[int]
    READING_VALUE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    sensor_name: str
    reading_value: str
    timestamp: str
    def __init__(self, sensor_name: _Optional[str] = ..., reading_value: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class DeviceRequest(_message.Message):
    __slots__ = ("type", "body")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    type: RequestType
    body: str
    def __init__(self, type: _Optional[_Union[RequestType, str]] = ..., body: _Optional[str] = ...) -> None: ...

class DeviceReply(_message.Message):
    __slots__ = ("status", "body")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    status: ReplyStatus
    body: str
    def __init__(self, status: _Optional[_Union[ReplyStatus, str]] = ..., body: _Optional[str] = ...) -> None: ...
