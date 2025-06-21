from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Address(_message.Message):
    __slots__ = ("ip", "port")
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class GatewayLocation(_message.Message):
    __slots__ = ("address",)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: Address
    def __init__(self, address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

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
    __slots__ = ("report_interval",)
    REPORT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    report_interval: int
    def __init__(self, report_interval: _Optional[int] = ...) -> None: ...
