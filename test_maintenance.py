"""Tests for maintenance-phase devices and parsing."""

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser


def build_model(source_text):
    """Build a simulator model from pasted source text."""
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    scanner = Scanner(None, names, source_text=source_text)
    parser = Parser(names, devices, network, monitors, scanner)
    assert parser.parse_network()
    return names, devices, network, monitors


def test_rc_device_falls_after_delay():
    """RC output starts high and falls low after its configured delay."""
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    [rc_id] = names.lookup(["ResetPulse"])

    assert devices.make_device(rc_id, devices.RC, 2) == devices.NO_ERROR
    assert network.get_output_signal(rc_id, None) == devices.HIGH

    network.execute_network()
    assert network.get_output_signal(rc_id, None) == devices.HIGH
    network.execute_network()
    assert network.get_output_signal(rc_id, None) == devices.HIGH
    network.execute_network()
    assert network.get_output_signal(rc_id, None) == devices.LOW


def test_siggen_repeats_binary_pattern():
    """SIGGEN cycles through its binary waveform pattern."""
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    [siggen_id] = names.lookup(["Pattern"])

    assert devices.make_device(siggen_id, devices.SIGGEN, "010") == \
        devices.NO_ERROR

    observed = []
    for _ in range(5):
        network.execute_network()
        observed.append(network.get_output_signal(siggen_id, None))

    assert observed == [
        devices.LOW,
        devices.HIGH,
        devices.LOW,
        devices.LOW,
        devices.HIGH,
    ]


def test_parser_accepts_rc_and_siggen():
    """Parser accepts RC and SIGGEN declarations in a full circuit."""
    source = """
DEVICES:
    ResetPulse = RC 3;
    Pattern = SIGGEN 0101;
    G1 = AND 2;
DEVICES END;

CONNECT:
    ResetPulse = G1.I1;
    Pattern = G1.I2;
CONNECT END;

MONITOR:
    ResetPulse;
    Pattern;
    G1;
MONITOR END;

END
"""
    names, devices, network, monitors = build_model(source)
    assert names.query("ResetPulse") in devices.find_devices(devices.RC)
    assert names.query("Pattern") in devices.find_devices(devices.SIGGEN)
    assert len(monitors.monitors_dictionary) == 3
