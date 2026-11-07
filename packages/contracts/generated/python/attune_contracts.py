"""Generated from packages/contracts/*. Do not edit by hand."""


SCHEMA_VERSION = 1

TARGET_KIND_ANDROID_CAR = "android_car"
TARGET_KIND_ROUTER_NODE = "router_node"
TARGET_KIND_ROUTER_LINE = "router_line"
TARGET_KIND_WINDOWS_DEVICE = "windows_device"

CAPABILITY_CAR_NAVIGATION_OPEN = "car.navigation.open"
CAPABILITY_CAR_NOTIFICATION_SHOW = "car.notification.show"
CAPABILITY_CAR_STATUS_READ = "car.status.read"
CAPABILITY_CAR_TTS_SPEAK = "car.tts.speak"
CAPABILITY_CAR_UI_OPEN = "car.ui.open"
CAPABILITY_ROUTER_CELLULAR_READ = "router.cellular.read"
CAPABILITY_ROUTER_CELLULAR_RECONNECT = "router.cellular.reconnect"
CAPABILITY_ROUTER_GNSS_READ = "router.gnss.read"
CAPABILITY_ROUTER_GNSS_START = "router.gnss.start"
CAPABILITY_ROUTER_GNSS_STOP = "router.gnss.stop"
CAPABILITY_ROUTER_NETWORK_READ = "router.network.read"
CAPABILITY_ROUTER_ROUTE_READ = "router.route.read"
CAPABILITY_ROUTER_ROUTE_SWITCH = "router.route.switch"
CAPABILITY_ROUTER_STATUS_READ = "router.status.read"
CAPABILITY_ROUTER_TELEPHONY_ANSWER = "router.telephony.answer"
CAPABILITY_ROUTER_TELEPHONY_DIAL = "router.telephony.dial"
CAPABILITY_ROUTER_TELEPHONY_DTMF = "router.telephony.dtmf"
CAPABILITY_ROUTER_TELEPHONY_HANGUP = "router.telephony.hangup"
CAPABILITY_ROUTER_TELEPHONY_SMS_SEND = "router.telephony.sms.send"
CAPABILITY_ROUTER_TELEPHONY_STATE = "router.telephony.state"


CAPABILITY_META = {
    CAPABILITY_CAR_NAVIGATION_OPEN: {
        "version": 1,
        "target_kind": TARGET_KIND_ANDROID_CAR,
        "class": "INTERACTION",
        "required_action": "device.operate",
        "data_class": "LOCATION",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "TERMINAL_ACK",
    },
    CAPABILITY_CAR_NOTIFICATION_SHOW: {
        "version": 1,
        "target_kind": TARGET_KIND_ANDROID_CAR,
        "class": "INTERACTION",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "TERMINAL_ACK",
    },
    CAPABILITY_CAR_STATUS_READ: {
        "version": 1,
        "target_kind": TARGET_KIND_ANDROID_CAR,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "DEVICE_METADATA",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
    CAPABILITY_CAR_TTS_SPEAK: {
        "version": 1,
        "target_kind": TARGET_KIND_ANDROID_CAR,
        "class": "INTERACTION",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "TERMINAL_ACK",
    },
    CAPABILITY_CAR_UI_OPEN: {
        "version": 1,
        "target_kind": TARGET_KIND_ANDROID_CAR,
        "class": "INTERACTION",
        "required_action": "device.operate",
        "data_class": "NON_SENSITIVE",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "TERMINAL_ACK",
    },
    CAPABILITY_ROUTER_CELLULAR_READ: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "DEVICE_METADATA",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
    CAPABILITY_ROUTER_CELLULAR_RECONNECT: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "DEVICE_METADATA",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_GNSS_READ: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "LOCATION",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
    CAPABILITY_ROUTER_GNSS_START: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "LOCATION",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_GNSS_STOP: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "LOCATION",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_NETWORK_READ: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "DEVICE_METADATA",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
    CAPABILITY_ROUTER_ROUTE_READ: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "DEVICE_METADATA",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
    CAPABILITY_ROUTER_ROUTE_SWITCH: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "CONFIG",
        "required_action": "device.config",
        "data_class": "DEVICE_METADATA",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_STATUS_READ: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_NODE,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "DEVICE_METADATA",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
    CAPABILITY_ROUTER_TELEPHONY_ANSWER: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_LINE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_TELEPHONY_DIAL: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_LINE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_TELEPHONY_DTMF: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_LINE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_TELEPHONY_HANGUP: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_LINE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_TELEPHONY_SMS_SEND: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_LINE,
        "class": "OPERATE",
        "required_action": "device.operate",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "BOUNDED_WRITE",
        "idempotency_required": True,
        "completion_evidence": "DEVICE_TRUTH",
    },
    CAPABILITY_ROUTER_TELEPHONY_STATE: {
        "version": 1,
        "target_kind": TARGET_KIND_ROUTER_LINE,
        "class": "READ",
        "required_action": "device.read",
        "data_class": "COMMUNICATION_CONTENT",
        "side_effect": "READ_ONLY",
        "idempotency_required": False,
        "completion_evidence": "READ_RESPONSE",
    },
}
