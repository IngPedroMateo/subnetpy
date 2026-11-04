import ipaddress

def calcular_subred(ip_str: str, prefijo: int) -> dict | None:
    """Calcula datos de subred tanto para IPv4 como para IPv6."""
    try:
        prefijo = int(prefijo)
        # ipaddress.ip_interface detecta automáticamente si es IPv4 o IPv6
        interface = ipaddress.ip_interface(f"{ip_str}/{prefijo}")
        red = interface.network

        id_red = red.network_address
        mascara = red.netmask
        hosts_totales = red.num_addresses
        es_ipv4 = isinstance(red, ipaddress.IPv4Network)

        if es_ipv4:
            broadcast = red.broadcast_address
            if prefijo == 31:
                hosts_asignables = 2
                rango_inicio = red.network_address
                rango_fin = red.broadcast_address
            elif prefijo == 32:
                hosts_asignables = 1
                rango_inicio = id_red
                rango_fin = id_red
            else:
                hosts_asignables = max(0, hosts_totales - 2)
                rango_inicio = id_red + 1
                rango_fin = broadcast - 1
        else:
            # IPv6 no utiliza la noción tradicional de broadcast (usa multicast)
            broadcast = "N/A (Multicast en IPv6)"
            if prefijo == 128:
                hosts_asignables = 1
                rango_inicio = id_red
                rango_fin = id_red
            elif prefijo == 127:  # RFC 6164 para enlaces P2P IPv6
                hosts_asignables = 2
                rango_inicio = id_red
                rango_fin = id_red + 1
            else:
                hosts_asignables = max(0, hosts_totales - 2)
                rango_inicio = id_red + 1
                rango_fin = red.broadcast_address

        return {
            "version": 4 if es_ipv4 else 6,
            "ip_ingresada": ip_str,
            "prefijo": prefijo,
            "mascara": mascara,
            "id_red": id_red,
            "broadcast": broadcast,
            "hosts_totales": hosts_totales,
            "hosts_asignables": hosts_asignables,
            "rango_inicio": rango_inicio,
            "rango_fin": rango_fin
        }

    except (ValueError, TypeError) as e:
        print(f"\nError al calcular la subred: ({e})")
        return None


def calcular_vlsm(red_base_str: str, requermientos_hosts: list[dict]) -> list[dict] | None:
    """
    Calcula la distribución de subredes VLSM ordenando los requerimientos de mayor a menor.
    requerimientos_hosts debe ser una lista de dicts: [{'nombre': 'LAN_1', 'hosts': 50}, ...]
    """
    try:
        # Detectar la red base (IPv4 o IPv6)
        red_actual = ipaddress.ip_network(red_base_str, strict=False)
        es_ipv4 = isinstance(red_actual, ipaddress.IPv4Network)
        max_prefijo = 32 if es_ipv4 else 128

        # Regra VLSM: Ordenar requerimientos de mayor a menor número de hosts
        reqs_ordenados = sorted(requermientos_hosts, key=lambda x: x['hosts'], reverse=True)
        subredes_resultantes = []

        posicion_ip = red_actual.network_address

        for req in reqs_ordenados:
            hosts_necesarios = req['hosts']
            nombre = req.get('nombre', 'Subred')

            # Calcular la cantidad total de IPs necesarias (sumando red/broadcast en IPv4)
            if es_ipv4:
                ips_necesarias = hosts_necesarios + 2 if hosts_necesarios > 2 else hosts_necesarios
            else:
                ips_necesarias = hosts_necesarios + 2

            # Encontrar el tamaño de sufijo/prefijo mínimo
            bits_host = (ips_necesarias - 1).bit_length()
            prefijo_subred = max_prefijo - bits_host

            # Crear el objeto de subred en la dirección IP libre actual
            subred = ipaddress.ip_network(f"{posicion_ip}/{prefijo_subred}", strict=False)

            # Verificar si se excede el espacio de la red base asignada
            if subred.network_address < red_actual.network_address or subred.broadcast_address > red_actual.broadcast_address:
                print(f"\nError: La subred '{nombre}' ({hosts_necesarios} hosts) no cabe en la red base.")
                return None

            # Obtener métricas detalladas usando la función base
            datos_subred = calcular_subred(str(subred.network_address), prefijo_subred)
            datos_subred["nombre"] = nombre
            datos_subred["hosts_solicitados"] = hosts_necesarios
            subredes_resultantes.append(datos_subred)

            # Mover el puntero de IP al siguiente bloque libre disponible
            posicion_ip = subred.broadcast_address + 1

        return subredes_resultantes

    except (ValueError, TypeError) as e:
        print(f"\nError en cálculo VLSM: ({e})")
        return None


# ==========================================
# Demostración de uso
# ==========================================
if __name__ == "__main__":
    print("=== 1. CÁLCULO DE SUBRED INDIVIDUAL (IPv4 / IPv6) ===")
    res_v4 = calcular_subred("192.168.1.45", 24)
    res_v6 = calcular_subred("2001:db8::1", 64)

    print(f"\nIPv4: ID Red = {res_v4['id_red']} | Hosts asignables = {res_v4['hosts_asignables']:,}")
    print(f"IPv6: ID Red = {res_v6['id_red']} | Hosts asignables = {res_v6['hosts_asignables']:,}")

    print("\n" + "=" * 60)
    print("=== 2. CÁLCULO DE VLSM ===")
    print("=" * 60)

    red_padre = "10.0.0.0/20"
    subredes_deseadas = [
        {"nombre": "Ventas", "hosts": 1000},
        {"nombre": "Soporte", "hosts": 500},
        {"nombre": "Servidores", "hosts": 50},
        {"nombre": "Enlace P2P", "hosts": 2}
    ]

    print(f"Red base para VLSM: {red_padre}\n")
    resultados_vlsm = calcular_vlsm(red_padre, subredes_deseadas)

    if resultados_vlsm:
        print(f"{'Nombre':<12} | {'Req. Hosts':<10} | {'Subred / CIDR':<18} | {'Máscara':<15} | {'Rango Útil':<30}")
        print("-" * 95)
        for s in resultados_vlsm:
            rango = f"{s['rango_inicio']} - {s['rango_fin']}"
            print(f"{s['nombre']:<12} | {s['hosts_solicitados']:<10} | {str(s['id_red']) + '/' + str(s['prefijo']):<18} | {str(s['mascara']):<15} | {rango:<30}")