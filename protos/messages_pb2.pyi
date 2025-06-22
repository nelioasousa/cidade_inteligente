from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RequestType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REQUESTTYPE_UNSPECIFIED: _ClassVar[RequestType]
    REQUESTTYPE_ACTION: _ClassVar[RequestType]
    REQUESTTYPE_GET_STATE: _ClassVar[RequestType]
    REQUESTTYPE_SET_STATE: _ClassVar[RequestType]
    REQUESTTYPE_GET_METADATA: _ClassVar[RequestType]
    REQUESTTYPE_SET_METADATA: _ClassVar[RequestType]

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATUS_UNSPECIFIED: _ClassVar[Status]
    STATUS_OK: _ClassVar[Status]
    STATUS_BAD: _ClassVar[Status]
    STATUS_FAIL: _ClassVar[Status]
    STATUS_DENIED: _ClassVar[Status]
    STATUS_UNKNOWN: _ClassVar[Status]
REQUESTTYPE_UNSPECIFIED: RequestType
REQUESTTYPE_ACTION: RequestType
REQUESTTYPE_GET_STATE: RequestType
REQUESTTYPE_SET_STATE: RequestType
REQUESTTYPE_GET_METADATA: RequestType
REQUESTTYPE_SET_METADATA: RequestType
STATUS_UNSPECIFIED: Status
STATUS_OK: Status
STATUS_BAD: Status
STATUS_FAIL: Status
STATUS_DENIED: Status
STATUS_UNKNOWN: Status

class Address(_message.Message):
    __slots__ = ("ip", "port")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ("name", "state", "metadata")
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    name: str
    state: str
    metadata: str
    def __init__(self, name: _Optional[str] = ..., state: _Optional[str] = ..., metadata: _Optional[str] = ...) -> None: ...

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
    report_interval: int
    def __init__(self, report_address: _Optional[_Union[Address, _Mapping]] = ..., report_interval: _Optional[int] = ...) -> None: ...

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
    __slots__ = ("type", "key", "value")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    type: RequestType
    key: str
    value: str
    def __init__(self, type: _Optional[_Union[RequestType, str]] = ..., key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class DeviceReply(_message.Message):
    __slots__ = ("status", "result")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    status: Status
    result: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., result: _Optional[str] = ...) -> None: ...
