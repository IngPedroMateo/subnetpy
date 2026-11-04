import ipaddress
from dataclasses import dataclass

@dataclass
class ResultadoSubred:
    ipv4_ingresada: str
    prefijo: int
    id_red: str
    broadcast: str
    mascara_subred: str
    hosts_totales: int
    hosts_disponibles: int
    rango_red: str


def calcular_detalles_ipv4(ip_str: str, prefijo: int | str) -> ResultadoSubred:
    """
    Calcula los datos clave de una subred IPv4 a partir de una IP y un prefijo CIDR.
    """
    # Limpiar el prefijo si se pasa en formato string como '/27' o '27'
    if isinstance(prefijo, str):
        prefijo_clean = int(prefijo.lstrip('/'))
    else:
        prefijo_clean = int(prefijo)

    # Validar rango del prefijo CIDR para IPv4
    if not (0 <= prefijo_clean <= 32):
        raise ValueError("El prefijo CIDR debe estar entre 0 y 32.")

    # Crear la interfaz combinada IP/Prefijo
    interface = ipaddress.IPv4Interface(f"{ip_str.strip()}/{prefijo_clean}")
    red = interface.network

    id_red = red.network_address
    broadcast = red.broadcast_address
    mascara = red.netmask
    hosts_totales = red.num_addresses

    # Reglas para prefijos especiales (/31 y /32)
    if prefijo_clean == 31:
        hosts_disponibles = 2
        rango_inicio = id_red
        rango_fin = broadcast
    elif prefijo_clean == 32:
        hosts_disponibles = 1
        rango_inicio = id_red
        rango_fin = id_red
    else:
        hosts_disponibles = max(0, hosts_totales - 2)
        rango_inicio = id_red + 1
        rango_fin = broadcast - 1

    rango_str = f"{rango_inicio} - {rango_fin}"

    return ResultadoSubred(
        ipv4_ingresada=str(interface.ip),
        prefijo=prefijo_clean,
        id_red=str(id_red),
        broadcast=str(broadcast),
        mascara_subred=str(mascara),
        hosts_totales=hosts_totales,
        hosts_disponibles=hosts_disponibles,
        rango_red=rango_str
    )


# ==========================================
# Ejemplo de uso con '192.168.200.154' y '/27'
# ==========================================
if __name__ == "__main__":
    ip_entrada = "192.168.200.154"
    prefijo_entrada = "/27"

    res = calcular_detalles_ipv4(ip_entrada, prefijo_entrada)

    print("=== RESULTADOS DEL CÁLCULO DE SUBRED ===")
    print(f"IPv4 Ingresada       : {res.ipv4_ingresada}/{res.prefijo}")
    print(f"ID de Red            : {res.id_red}")
    print(f"Broadcast            : {res.broadcast}")
    print(f"Máscara de Subred    : {res.mascara_subred}")
    print(f"Hosts Totales        : {res.hosts_totales}")
    print(f"Hosts Disponibles    : {res.hosts_disponibles}")
    print(f"Rango de Red Útil    : {res.rango_red}")