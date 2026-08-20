import time
import mysql.connector

from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    MYSQL_CLOUD_HOST, MYSQL_CLOUD_USER, MYSQL_CLOUD_PASSWORD, MYSQL_CLOUD_DATABASE
)

def connect_local():
    """Liga-se ao MySQL local."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
            password=MYSQL_PASSWORD, database=MYSQL_DATABASE, autocommit=True
        )
        return conn
    except Exception as e:
        print(f"[!] Erro ao ligar ao MySQL local: {e}")
        return None

def fetch_and_setup():
    local_conn = connect_local()
    if not local_conn:
        print("[FATAL] Não foi possível ligar ao MySQL local. Abortando setup.")
        return False

    try:
        print(f"A ligar à base de dados da Nuvem em {MYSQL_CLOUD_HOST}...")
        cloud_conn = mysql.connector.connect(
            host=MYSQL_CLOUD_HOST, user=MYSQL_CLOUD_USER,
            password=MYSQL_CLOUD_PASSWORD, database=MYSQL_CLOUD_DATABASE,
            connection_timeout=5
        )
        
        if cloud_conn.is_connected():
            print("[✓] Ligado à Nuvem com sucesso! A descarregar Mapa e Configurações...")
            cloud_cursor = cloud_conn.cursor(dictionary=True)
            local_cursor = local_conn.cursor()

            # 1. SetupMaze
            cloud_cursor.execute("SELECT * FROM SetupMaze LIMIT 1")
            setup = cloud_cursor.fetchone()
            if setup:
                nr_rooms = setup.get("numberrooms", 10)
                local_cursor.callproc("sp_inserir_setupmaze", [
                    nr_rooms,
                    setup.get("numbermarsamis", 30),
                    setup.get("numberplayers", 40),
                    float(setup.get("normaltemperature", 20.0)),
                    float(setup.get("temperaturevarhightoleration", 5.0)),
                    float(setup.get("temperaturevarlowtoleration", 5.0)),
                    float(setup.get("normalnoise", 15.0)),
                    float(setup.get("noisevartoleration", 5.0))
                ])
                print("   ↳ SetupMaze importado da Nuvem.")
                
                # ID Setup
                local_cursor.execute("SELECT MAX(idSetup) FROM setupmaze")
                max_setup_row = local_cursor.fetchone()
                id_setup = max_setup_row[0] if max_setup_row and max_setup_row[0] else 1

                # Encontrar a simulação que o utilizador acabou de iniciar (IsActive = 0)
                local_cursor.execute("SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1")
                sim_row = local_cursor.fetchone()
                
                if sim_row:
                    id_simulacao = sim_row[0]
                    # Associar este Setup à simulação em curso
                    local_cursor.execute("UPDATE simulacao SET IDSetup = %s WHERE idSimulacao = %s", (id_setup, id_simulacao))
                    
                    # Preencher Salas (de 1 a nr_rooms, sem a sala 0 que é apenas o spawner)
                    for room_id in range(1, nr_rooms + 1):
                        local_cursor.execute("INSERT IGNORE INTO ocupacaolabirinto (idSimulacao, idSala, nrMarsamisOdd, nrMarsamisEven, tentativasPontuacao) VALUES (%s, %s, 0, 0, 0)", (id_simulacao, room_id))
                    
                    print(f"   ↳ SetupMaze associado à Simulação em curso #{id_simulacao} com {nr_rooms} salas preparadas!")
                else:
                    print("   ↳ Nenhuma simulação 'A decorrer' encontrada para associar o Setup.")

            # 2. Corredores
            cloud_cursor.execute("SELECT * FROM Corridor")
            corridors = cloud_cursor.fetchall()
            for c in corridors:
                roomA = c.get("Rooma", 0)
                roomB = c.get("Roomb", 0)
                # Ignorar ligações vazias por segurança
                if roomA != 0 or roomB != 0:
                    local_cursor.callproc("sp_inserir_corredor_mapa", [roomA, roomB])
            print(f"   ↳ Mapa de Corredores importado ({len(corridors)} ligações).")

            cloud_cursor.close()
            local_cursor.close()
            cloud_conn.close()
            local_conn.close()
            return True

    except Exception as e:
        print(f"[!] AVISO: A Nuvem não respondeu ({e}). A criar Simulação de Emergência Local...")
        try:
            local_cursor = local_conn.cursor()
            local_cursor.execute("UPDATE simulacao SET IsActive = 0 WHERE IsActive = 1")
            local_cursor.execute("INSERT IGNORE INTO setupmaze (idSetup, nrRooms, nrMarsamis, nrPlayers, normalTemp, tempVarHighTol, tempVarLowTol, normalSom, somVarTol) VALUES (1, 10, 30, 1, 20.0, 5.0, 5.0, 40.0, 10.0)")
            local_cursor.execute("SELECT MAX(idSetup) FROM setupmaze")
            id_setup = local_cursor.fetchone()[0] or 1
            local_cursor.execute("SELECT idSimulacao FROM simulacao WHERE IsActive = 0 LIMIT 1")
            sim_row = local_cursor.fetchone()
            if sim_row:
                id_simulacao = sim_row[0]
                local_cursor.execute("UPDATE simulacao SET IDSetup = %s WHERE idSimulacao = %s", (id_setup, id_simulacao))
                for room_id in range(1, 11):
                    local_cursor.execute("INSERT IGNORE INTO ocupacaolabirinto (idSimulacao, idSala, nrMarsamisOdd, nrMarsamisEven, tentativasPontuacao) VALUES (%s, %s, 0, 0, 0)", (id_simulacao, room_id))
                print(f"   ↳ Setup Local associado à Simulação #{id_simulacao} com sucesso!")
            local_cursor.close()
            local_conn.close()
            return True
        except Exception as inner_e:
            print(f"[!] ERRO CRÍTICO no Fallback Local: {inner_e}")
            local_conn.close()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("  SCRIPT 0, SETUP INICIAL (Sincronização com a Nuvem)")
    print("=" * 60)
    success = fetch_and_setup()
    if success:
        print("\n[✓] SETUP CONCLUÍDO. O sistema pode arrancar!\n")
    else:
        print("\n[!] O SETUP FALHOU. Por favor verifica a base de dados.\n")
    time.sleep(2)
