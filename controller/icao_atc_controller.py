import time
from datetime import datetime
from bluesky.simulation import simulation
from bluesky.traffic import Traffic

# Inicializa log
print(f"[{datetime.utcnow().isoformat()}Z] ICAO-based ATC controller started.")

# Instância do tráfego (Traffic é um singleton)
traffic = Traffic.instance

# Critérios de separação mínima
MIN_HORIZONTAL_SEPARATION = 5.0  # milhas náuticas
MIN_VERTICAL_SEPARATION = 1000.0  # pés

# Função para detectar e resolver conflitos de separação
def resolve_conflict(ac1, ac2):
    # Cálculo horizontal
    dx = ac1.x - ac2.x
    dy = ac1.y - ac2.y
    horizontal_dist = (dx**2 + dy**2)**0.5

    # Cálculo vertical
    vertical_dist = abs(ac1.alt - ac2.alt)

    if horizontal_dist < MIN_HORIZONTAL_SEPARATION and vertical_dist < MIN_VERTICAL_SEPARATION:
        print(f"[CONFLICT] {ac1.id} vs {ac2.id} | Horiz: {horizontal_dist:.2f}nm Vert: {vertical_dist:.0f}ft")

        # Estratégia simples: altera heading do ac1
        old_heading = ac1.hdg
        ac1.sethdg(old_heading + 10)
        print(f"[ACTION] Adjusted heading of {ac1.id} from {old_heading} to {ac1.hdg}")

# Função para verificar se a aeronave chegou ao destino
def reached_destination(ac):
    if ac.destx is None or ac.desty is None:
        return False
    dx = ac.x - ac.destx
    dy = ac.y - ac.desty
    horizontal_dist = (dx**2 + dy**2)**0.5
    return horizontal_dist < 1.0  # 1 milha náutica de tolerância

def controller_update():
    active_ac = list(traffic)
    print(f"[{datetime.utcnow().isoformat()}Z] Active aircraft: {[ac.id for ac in active_ac]}")

    for i, ac1 in enumerate(active_ac):
        # Verifica se chegou ao destino
        if reached_destination(ac1):
            print(f"[INFO] Aircraft {ac1.id} reached destination. Removing...")
            ac1.delac()
            continue

        # Verifica conflitos com outras aeronaves
        for j in range(i + 1, len(active_ac)):
            ac2 = active_ac[j]
            resolve_conflict(ac1, ac2)

# Executa em loop
while True:
    controller_update()
    time.sleep(1.0)
