#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
import os
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

def parse_ethernet_header(data):
    dest_mac = data[0:6]
    src_mac = data[6:12]
    ether_type = (data[12] << 8) + data[13]
    vlan_id = -1

    if ether_type == 0x8200:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def is_unicast(mac):
    return (mac[0] & 1) == 0

def load_configuration(switch_id):
    config_path = f'configs/switch{switch_id}.cfg'
    vlan_map = {}
    trunk_ports = set()

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) == 2:
                        interface, vlan_or_trunk = parts
                        if vlan_or_trunk == 'T':
                            trunk_ports.add(interface)
                        else:
                            vlan_map[interface] = int(vlan_or_trunk)
        print(f"[INFO] Loaded configuration for switch {switch_id}")
    except FileNotFoundError:
        print(f"[ERROR] Configuration file {config_path} not found.")
    except ValueError:
        print(f"[ERROR] Invalid configuration format in {config_path}")

    return vlan_map, trunk_ports

def main():
    switch_id = sys.argv[1]
    config_file = f'configs/switch{switch_id}.cfg'
    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC", ':'.join(f'{b:02x}' for b in get_switch_mac()))

    vlan_map, trunk_ports = load_configuration(switch_id)
    mac_table = {}

    while True:
        interface, data, length = recv_from_any_link()
        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

        interface_name = get_interface_name(interface)
        if interface_name in vlan_map:
            port_vlan_id = vlan_map[interface_name]
            if vlan_id == -1:
                vlan_id = port_vlan_id
                data = data[:12] + create_vlan_tag(vlan_id) + data[12:]
                length += 4
            elif vlan_id != port_vlan_id:
                continue
        elif interface_name in trunk_ports:
            port_vlan_id = vlan_id

        dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac = ':'.join(f'{b:02x}' for b in src_mac)
        print(f'Destination MAC: {dest_mac}')
        print(f'Source MAC: {src_mac}')
        print(f'EtherType: {ethertype}')
        print(f'VLAN ID: {vlan_id}')
        print("Received frame of size {} on interface {}".format(length, interface), flush=True)

        mac_table[(src_mac, vlan_id)] = interface

        if is_unicast(data[0:6]):
            if (dest_mac, vlan_id) in mac_table:
                out_port = mac_table[(dest_mac, vlan_id)]
                out_interface_name = get_interface_name(out_port)
                if out_interface_name in vlan_map:
                    if vlan_id == vlan_map[out_interface_name]:
                        data = data[:12] + data[16:]
                        length -= 4
                send_to_link(out_port, length, data)
            else:
                for port in interfaces:
                    if port != interface:
                        out_interface_name = get_interface_name(port)
                        if out_interface_name in trunk_ports or (
                            out_interface_name in vlan_map and vlan_map[out_interface_name] == vlan_id
                        ):
                            if out_interface_name in vlan_map:
                                data_to_send = data[:12] + data[16:] if vlan_id == vlan_map[out_interface_name] else data
                                adjusted_length = length - 4 if vlan_id == vlan_map[out_interface_name] else length
                            else:
                                data_to_send = data
                                adjusted_length = length
                            send_to_link(port, adjusted_length, data_to_send)
        else:
            for port in interfaces:
                if port != interface:
                    out_interface_name = get_interface_name(port)
                    if out_interface_name in trunk_ports or (
                        out_interface_name in vlan_map and vlan_map[out_interface_name] == vlan_id
                    ):
                        if out_interface_name in vlan_map:
                            data_to_send = data[:12] + data[16:] if vlan_id == vlan_map[out_interface_name] else data
                            adjusted_length = length - 4 if vlan_id == vlan_map[out_interface_name] else length
                        else:
                            data_to_send = data
                            adjusted_length = length
                        send_to_link(port, adjusted_length, data_to_send)

if __name__ == "__main__":
    main()
