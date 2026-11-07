// Generated from packages/contracts/*. Do not edit by hand.
package ai.attune.contracts.generated

object AttuneContractV1 {
    const val SCHEMA_VERSION: Int = 1

    object TargetKind {
        const val ANDROID_CAR: String = "android_car"
        const val ROUTER_NODE: String = "router_node"
        const val ROUTER_LINE: String = "router_line"
        const val WINDOWS_DEVICE: String = "windows_device"
    }

    object Capability {
        const val CAR_NAVIGATION_OPEN: String = "car.navigation.open"
        const val CAR_NOTIFICATION_SHOW: String = "car.notification.show"
        const val CAR_STATUS_READ: String = "car.status.read"
        const val CAR_TTS_SPEAK: String = "car.tts.speak"
        const val CAR_UI_OPEN: String = "car.ui.open"
        const val ROUTER_CELLULAR_READ: String = "router.cellular.read"
        const val ROUTER_CELLULAR_RECONNECT: String = "router.cellular.reconnect"
        const val ROUTER_GNSS_READ: String = "router.gnss.read"
        const val ROUTER_GNSS_START: String = "router.gnss.start"
        const val ROUTER_GNSS_STOP: String = "router.gnss.stop"
        const val ROUTER_NETWORK_READ: String = "router.network.read"
        const val ROUTER_ROUTE_READ: String = "router.route.read"
        const val ROUTER_ROUTE_SWITCH: String = "router.route.switch"
        const val ROUTER_STATUS_READ: String = "router.status.read"
        const val ROUTER_TELEPHONY_ANSWER: String = "router.telephony.answer"
        const val ROUTER_TELEPHONY_DIAL: String = "router.telephony.dial"
        const val ROUTER_TELEPHONY_DTMF: String = "router.telephony.dtmf"
        const val ROUTER_TELEPHONY_HANGUP: String = "router.telephony.hangup"
        const val ROUTER_TELEPHONY_SMS_SEND: String = "router.telephony.sms.send"
        const val ROUTER_TELEPHONY_STATE: String = "router.telephony.state"
    }

    data class CapabilityMeta(
        val version: Int,
        val targetKind: String,
        val capabilityClass: String,
        val requiredAction: String,
        val dataClass: String,
        val sideEffect: String,
        val idempotencyRequired: Boolean,
        val completionEvidence: String,
    )

    val CAPABILITY_META: Map<String, CapabilityMeta> = mapOf(
        Capability.CAR_NAVIGATION_OPEN to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ANDROID_CAR,
            capabilityClass = "INTERACTION",
            requiredAction = "device.operate",
            dataClass = "LOCATION",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "TERMINAL_ACK",
        ),
        Capability.CAR_NOTIFICATION_SHOW to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ANDROID_CAR,
            capabilityClass = "INTERACTION",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "TERMINAL_ACK",
        ),
        Capability.CAR_STATUS_READ to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ANDROID_CAR,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "DEVICE_METADATA",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
        Capability.CAR_TTS_SPEAK to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ANDROID_CAR,
            capabilityClass = "INTERACTION",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "TERMINAL_ACK",
        ),
        Capability.CAR_UI_OPEN to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ANDROID_CAR,
            capabilityClass = "INTERACTION",
            requiredAction = "device.operate",
            dataClass = "NON_SENSITIVE",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "TERMINAL_ACK",
        ),
        Capability.ROUTER_CELLULAR_READ to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "DEVICE_METADATA",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
        Capability.ROUTER_CELLULAR_RECONNECT to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "DEVICE_METADATA",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_GNSS_READ to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "LOCATION",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
        Capability.ROUTER_GNSS_START to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "LOCATION",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_GNSS_STOP to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "LOCATION",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_NETWORK_READ to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "DEVICE_METADATA",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
        Capability.ROUTER_ROUTE_READ to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "DEVICE_METADATA",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
        Capability.ROUTER_ROUTE_SWITCH to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "CONFIG",
            requiredAction = "device.config",
            dataClass = "DEVICE_METADATA",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_STATUS_READ to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_NODE,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "DEVICE_METADATA",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
        Capability.ROUTER_TELEPHONY_ANSWER to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_LINE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_TELEPHONY_DIAL to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_LINE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_TELEPHONY_DTMF to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_LINE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_TELEPHONY_HANGUP to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_LINE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_TELEPHONY_SMS_SEND to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_LINE,
            capabilityClass = "OPERATE",
            requiredAction = "device.operate",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "BOUNDED_WRITE",
            idempotencyRequired = true,
            completionEvidence = "DEVICE_TRUTH",
        ),
        Capability.ROUTER_TELEPHONY_STATE to CapabilityMeta(
            version = 1,
            targetKind = TargetKind.ROUTER_LINE,
            capabilityClass = "READ",
            requiredAction = "device.read",
            dataClass = "COMMUNICATION_CONTENT",
            sideEffect = "READ_ONLY",
            idempotencyRequired = false,
            completionEvidence = "READ_RESPONSE",
        ),
    )
}
