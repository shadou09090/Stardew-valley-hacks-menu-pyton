import pymem
import pymem.pattern
from pymem.process import module_from_name
import threading
import time
import ctypes


def virtual_protect(handle, address, size, protection):
    old_protect = ctypes.c_ulong(0)
    resultado = ctypes.windll.kernel32.VirtualProtectEx(
        handle,
        ctypes.c_void_p(address),
        ctypes.c_size_t(size),
        ctypes.c_ulong(protection),
        ctypes.byref(old_protect)
    )
    if not resultado:
        raise Exception("Fallo al cambiar los permisos de memoria.")
    return old_protect.value


# --- VARIABLES GLOBALES PARA CONGELAR ---
congelar_plata = False
congelar_energia = False
congelar_tiempo = False
congelar_vida = False
valor_plata_fija = 99999
valor_energia_fija = 999.0
valor_tiempo_fijo = 600
valor_vida_fija = 100.0

direccion_plata_global = 0
direccion_energia_global = 0
direccion_tiempo_global = 0
direccion_vida_global = 0


def find_dynamic_address(pm, base_ptr, offsets):
    """Resuelve la cadena de punteros"""
    addr = base_ptr
    for i, offset in enumerate(offsets):
        try:
            next_addr = pm.read_ulonglong(addr)
            addr = next_addr + offset
        except Exception:
            return 0
    return addr


def toggle_item_hack(pm, addr, activar):
    """Activa o desactiva la inyección AOB de los items"""
    original = b"\x89\x56\x4C"
    nops = b"\x90\x90\x90"

    virtual_protect(pm.process_handle, addr, 3, 0x40)
    if activar:
        pm.write_bytes(addr, nops, 3)
    else:
        pm.write_bytes(addr, original, 3)


def freezer_thread(pm):
    """Este hilo corre en segundo plano y congela los valores si están activados"""
    global congelar_plata, congelar_energia, congelar_tiempo, congelar_vida, direccion_plata_global, direccion_energia_global, direccion_tiempo_global, direccion_vida_global

    while True:
        try:
            if congelar_plata and direccion_plata_global != 0:
                pm.write_int(direccion_plata_global, valor_plata_fija)

            if congelar_energia and direccion_energia_global != 0:
                pm.write_float(direccion_energia_global, valor_energia_fija)

            if congelar_tiempo and direccion_tiempo_global != 0:
                pm.write_int(direccion_tiempo_global, valor_tiempo_fijo)

            if congelar_vida and direccion_vida_global != 0:
                pm.write_float(direccion_vida_global, valor_vida_fija)

        except Exception:
            pass

        time.sleep(0.01)


def main():
    global direccion_plata_global, direccion_energia_global, direccion_tiempo_global, direccion_vida_global
    global congelar_plata, congelar_energia, congelar_tiempo, congelar_vida, valor_plata_fija, valor_energia_fija, valor_tiempo_fijo, valor_vida_fija

    try:
        pm = pymem.Pymem("Stardew Valley.exe")
    except Exception:
        print("[-] No se encontro el juego ejecutandose.")
        return

    coreclr = module_from_name(pm.process_handle, "coreclr.dll")
    if not coreclr:
        print("[-] No se encontro coreclr.dll.")
        return

    print("[+] Buscando funciones en memoria...")

    aob_items = b"\x89\x56\x4C\x48\x83\xC4\x20"
    items_addr = pymem.pattern.pattern_scan_all(pm.process_handle, aob_items)
    if items_addr:
        print(f"[+] Funcion de items encontrada: 0x{items_addr:X}")
    else:
        print("[-] Funcion de items no encontrada.")

    # Configurar offsets
    base_address = coreclr.lpBaseOfDll + 0x0049D188
    base_address2 = coreclr.lpBaseOfDll + 0x004A9F90
    base_address3 = coreclr.lpBaseOfDll + 0x0049D188
    base_address4 = coreclr.lpBaseOfDll + 0x0049D188

    offsets_plata = [0xC8, 0x68, 0x90, 0x28C, 0x10, 0x4C0, 0x41C]
    offsets_tiempo = [0x110, 0x5A0, 0x48, 0x88, 0x20, 0x308, 0x8F4]
    offsets_energia = [0x2E8, 0x40, 0xB0, 0xA44, 0x10, 0x478, 0x4D4]
    offsets_vida = [0x458, 0x40, 0x90, 0x40, 0xBF0, 0x0, 0x6EC]

    # Resolver direcciones
    direccion_plata_global = find_dynamic_address(pm, base_address, offsets_plata)
    direccion_tiempo_global = find_dynamic_address(pm, base_address2, offsets_tiempo)
    direccion_energia_global = find_dynamic_address(pm, base_address3, offsets_energia)
    direccion_vida_global = find_dynamic_address(pm, base_address4, offsets_vida)

    hilo = threading.Thread(target=freezer_thread, args=(pm,), daemon=True)
    hilo.start()

    while True:
        print("\n" + "=" * 30)
        print("      STARDEW VALLEY PRO      ")
        print("=" * 30)
        print("1. Modificar Tiempo (Una vez)")
        print("2. Modificar Plata (Una vez)")
        print("3. Modificar Energia (Una vez)")
        print("4. Modificar Vida (Una vez)")
        print(f"5. Congelar Plata: {'[ACTIVADO]' if congelar_plata else '[DESACTIVADO]'}")
        print(f"6. Congelar Energia: {'[ACTIVADO]' if congelar_energia else '[DESACTIVADO]'}")
        print(f"7. Congelar Tiempo: {'[ACTIVADO]' if congelar_tiempo else '[DESACTIVADO]'}")
        print(f"8. Congelar Vida: {'[ACTIVADO]' if congelar_vida else '[DESACTIVADO]'}")
        print("9. Items/Agua Infinitos (Activar)")
        print("10. Items/Agua Normales (Desactivar)")
        print("11. Salir")

        op = input("\nElige una opcion: ")

        try:
            if op == "1":
                if direccion_tiempo_global:
                    t = int(input("Tiempo (ej. 600): "))
                    pm.write_int(direccion_tiempo_global, t)
                    print("[!] Tiempo cambiado.")
                else:
                    print("[-] Direccion de tiempo no valida.")

            elif op == "2":
                if direccion_plata_global:
                    p = int(input("Cuanta plata quieres: "))
                    pm.write_int(direccion_plata_global, p)
                    print("[!] Plata cambiada.")
                else:
                    print("[-] Direccion de plata no valida.")

            elif op == "3":
                if direccion_energia_global:
                    e = float(input("Cuanta energia quieres: "))
                    pm.write_float(direccion_energia_global, e)
                    print("[!] Energia cambiada.")
                else:
                    print("[-] Direccion de energia no valida.")

            elif op == "4":
                if direccion_vida_global:
                    v = int(input("Cuanta vida quieres: "))
                    pm.write_int(direccion_vida_global, v)
                    print("[!] Vida cambiada.")
                else:
                    print("[-] Direccion de vida no valida.")

            elif op == "5":
                global valor_plata_fija
                congelar_plata = not congelar_plata
                if congelar_plata:
                    valor_plata_fija = int(input("En que cantidad quieres congelar la plata?: "))
                print(f"[!] Congelar Plata es ahora: {congelar_plata}")

            elif op == "6":
                global valor_energia_fija
                congelar_energia = not congelar_energia
                if congelar_energia:
                    valor_energia_fija = float(input("En que cantidad quieres congelar la energia?: "))
                print(f"[!] Congelar Energia es ahora: {congelar_energia}")

            elif op == "7":
                global valor_tiempo_fijo
                congelar_tiempo = not congelar_tiempo
                if congelar_tiempo:
                    valor_tiempo_fijo = int(input("En que tiempo quieres congelar el reloj? (ej. 1300 para 1:00 PM): "))
                print(f"[!] Congelar Tiempo es ahora: {congelar_tiempo}")

            elif op == "8":
                global valor_vida_fija
                congelar_vida = not congelar_vida
                if congelar_vida:
                    valor_vida_fija = int(input("En que cantidad quieres congelar la vida?: "))
                print(f"[!] Congelar Vida es ahora: {congelar_vida}")

            elif op == "9":
                if items_addr:
                    toggle_item_hack(pm, items_addr, True)
                    print("[!] Items infinitos ACTIVADOS.")
                else:
                    print("[-] No se puede activar, direccion no encontrada.")

            elif op == "10":
                if items_addr:
                    toggle_item_hack(pm, items_addr, False)
                    print("[!] Items infinitos DESACTIVADOS.")

            elif op == "11":
                print("Restaurando memoria y saliendo...")
                if items_addr:
                    toggle_item_hack(pm, items_addr, False)
                break

            else:
                print("[-] Opcion invalida.")

        except Exception as e:
            print(f"[-] Ocurrio un error en la escritura: {e}")


if __name__ == "__main__":
    main()