## Running

```bash
sudo python3 checker/topo.py
```

This will open 9 terminals, 6 hosts and 3 for the switches. On the switch terminal you will run 

```bash
make run_switch SWITCH_ID=X # X is 0,1 or 2
```

The hosts have the following IP addresses.
```
host0 192.168.1.1
host1 192.168.1.2
host2 192.168.1.3
host3 192.168.1.4
host4 192.168.1.5
host5 192.168.1.6
```

We will be testing using the ICMP. For example, from host0 we will run:

```
ping 192.168.1.2
```

Note: We will use wireshark for debugging. From any terminal you can run `wireshark&`.



### 1. Procesul de Comutare
## Logica:
- La primirea unui cadru, adresa MAC sursă este salvată în `mac_table`.
- Dacă destinația este cunoscută (unicast), cadrul este direcționat către portul asociat.
- Dacă destinația este necunoscută, cadrul este trimis (flooded) către toate porturile, exceptând cel de intrare.
 **`is_unicast(mac)`**: Verifică dacă adresa MAC este unicast, necesară pentru a determina dacă traficul trebuie direcționat către un port specific.

### 2. VLAN
## Logica:
- Dacă cadrul este primit pe un port de acces și este neetichetat, se adaugă tag-ul VLAN corespunzător.
- Cadrul este transmis doar către porturile cu același VLAN ID sau către porturile trunk, menținând izolarea traficului între VLAN-uri.
- **`load_configuration(switch_id)`**: Încarcă configurațiile VLAN din fișierele `configs/switch<switch_id>.cfg`, definind maparea VLAN pentru fiecare port și identificând porturile trunk.
- **Modificări de lungime și date pentru VLAN**: Dacă un cadru este neetichetat pe un port de acces, este tag-uit cu VLAN-ul portului. La trimiterea pe un port de acces, tag-ul VLAN este eliminat.
