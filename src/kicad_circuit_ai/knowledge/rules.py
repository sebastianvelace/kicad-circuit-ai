"""Net name normalization and generic validation rules."""

# Nets that are equivalent to GND (ground potential)
GND_NETS = frozenset({
    "GND", "GND0", "GNDA", "AGND", "DGND", "PGND",
    "EARTH", "VSS", "0V", "GND_POWER", "PE",
})

# Nets that are equivalent to a positive supply (VCC-type)
VCC_NETS = frozenset({
    "VCC", "VDD", "AVCC", "DVCC", "+5V", "+3V3", "+3.3V",
    "+5VD", "+3V", "+12V", "+9V", "+15V", "+24V",
    "VBUS", "V+", "VSYS", "VIN",
})

# Nets that are equivalent to a negative supply
V_MINUS_NETS = frozenset({
    "V-", "VEE", "-5V", "-12V", "-15V", "-9V",
})


def normalize_net(net_name: str) -> str:
    """Return a canonical net category name or the original net name."""
    upper = net_name.strip().upper()
    if upper in GND_NETS:
        return "GND"
    if upper in VCC_NETS:
        return "VCC"
    if upper in V_MINUS_NETS:
        return "V_MINUS"
    return net_name


def is_gnd(net_name: str) -> bool:
    return normalize_net(net_name) == "GND"


def is_vcc(net_name: str) -> bool:
    return normalize_net(net_name) == "VCC"


def is_floating(net_name: str) -> bool:
    """A net is floating when it has no name or is an unconnected placeholder."""
    stripped = net_name.strip().upper()
    return not stripped or stripped in ("UNCONNECTED", "NC", "?", "~")


def net_matches(net_name: str, expected: str) -> bool:
    """Check if net_name matches expected, applying normalization."""
    norm_actual = normalize_net(net_name)
    norm_expected = normalize_net(expected)
    return norm_actual == norm_expected or net_name.upper() == expected.upper()
