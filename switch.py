#!/usr/bin/python3
import sys
import struct
import wrapper
import threading
import time
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

# Tabel de forwarding pentru învățarea adreselor MAC
forwarding_table = {}
vlan_table = {}  # Tabel pentru VLAN-uri, unde cheia este VLAN ID și valoarea o listă de interfețe

# Timeout pentru adresele MAC în secunde
MAC_TIMEOUT = 300

def parse_ethernet_header(data):
    dest_mac = data[0:6]
    src_mac = data[6:12]
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    if ether_type == 0x8100:
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    return struct.pack('!H', 0x8100) + struct.pack('!H', vlan_id & 0x0FFF)

def send_bdpu_every_sec():
    while True:
        bpdu_data = b'\x01\x80\xc2\x00\x00\x00' + get_switch_mac()  # Exemplu de BPDU
        for i in range(num_interfaces):
            send_to_link(i, len(bpdu_data), bpdu_data)
        time.sleep(1)

def main():
    switch_id = sys.argv[1]
    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(num_interfaces)
    print("# Starting switch with id {}".format(switch_id), flush=True)
    print("[INFO] Switch MAC:", ':'.join(f'{b:02x}' for b in get_switch_mac()))

    # Inițiere fir pentru trimitere BPDU
    threading.Thread(target=send_bdpu_every_sec, daemon=True).start()

    while True:
        interface, data, length = recv_from_any_link()

        dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

        # MAC learning
        forwarding_table[src_mac] = (interface, time.time())

        # Ștergerea adreselor MAC expirate
        for mac in list(forwarding_table.keys()):
            if time.time() - forwarding_table[mac][1] > MAC_TIMEOUT:
                del forwarding_table[mac]

        # Conversia adreselor MAC la format uman
        dest_mac_str = ':'.join(f'{b:02x}' for b in dest_mac)
        src_mac_str = ':'.join(f'{b:02x}' for b in src_mac)
        print(f'Destination MAC: {dest_mac_str}, Source MAC: {src_mac_str}, EtherType: {ethertype}, VLAN ID: {vlan_id}')

        # VLAN support: Rutează cadrele în funcție de VLAN ID
        if vlan_id != -1:
            if vlan_id not in vlan_table:
                vlan_table[vlan_id] = []
            vlan_table[vlan_id].append(interface)
            # Rutează cadrul pe interfețele din același VLAN
            for i in vlan_table[vlan_id]:
                if i != interface:
                    send_to_link(i, length, data)
        else:
            # Forwarding simplu pe baza MAC
            if dest_mac in forwarding_table:
                out_interface, _ = forwarding_table[dest_mac]
                send_to_link(out_interface, length, data)
            else:
                # Flooding dacă MAC-ul nu este cunoscut
                for i in interfaces:
                    if i != interface:
                        send_to_link(i, length, data)

if __name__ == "__main__":
    main()
