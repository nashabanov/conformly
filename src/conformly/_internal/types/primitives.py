from enum import Enum

FieldPath = tuple[int, ...]


class FieldKind(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ENUM = "enum"
    UUID = "uuid"

    # special strings
    EMAIL = "email"
    IPv4 = "ipv4"
    IPv6 = "ipv6"
    IPvAny = "ipvany"
    URL = "url"
    HTTPURL = "httpurl"

    # collections
    LIST = "list"


class ViolationType(Enum):
    # numeric
    BELOW_MIN = "below_min"
    ABOVE_MAX = "above_max"
    NOT_MULTIPLE = "not_multiple"

    # string
    TOO_LONG = "too_long"
    TOO_SHORT = "too_short"
    PATTERN_MISMATCH = "pattern_mismatch"

    # email
    WRONG_EMAIL_FORMAT = "wrong_email_format"

    # ip
    WRONG_IP_FORMAT = "wrong_ip_format"

    # url
    WRONG_URL_FORMAT = "wrong_url_format"
    WRONG_URL_SCHEME = "wrong_url_scheme"

    # uuid
    WRONG_UUID_FORMAT = "wrong_uuid_format"
    WRONG_UUID_CHARACTER = "wrong_uuid_character"

    # typing
    TYPE_MISMATCH = "type_mismatch"
    NONE_FOR_NOT_OPTIONAL = "none_for_not_optional"

    # Enum
    NOT_ALLOWED_VALUE = "not_allowed_value"

    # collections
    TOO_LESS_ITEMS = "too_less_items"
    TOO_MANY_ITEMS = "too_many_items"
    DUPLICATE = "duplicate"

    # structural
    MISSING_FIELD = "missing_field"
    EXTRA_FIELD = "extra_field"
