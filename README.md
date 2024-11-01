1 2

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
