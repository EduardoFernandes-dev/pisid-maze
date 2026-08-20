import json
import time
import threading
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import warnings
from backup_manager import BackupManager

warnings.filterwarnings("ignore", category=DeprecationWarning)

from config import (
    GROUP_NUMBER,
    MQTT_BROKER_LOCAL, MQTT_PORT_LOCAL,
    MONGO_URI, MONGO_DB_NAME,
    TOPIC_OUT_MOV, TOPIC_OUT_TEMP, TOPIC_OUT_SOUND,
    TOPIC_IN_MOV, TOPIC_IN_TEMP, TOPIC_IN_SOUND,
)

# Mapeamento: Coleção no MongoDB -> Tópico de Origem + Tópico de Saída
COLLECTIONS_MAP = {
    "movements":   {"topic_origin": TOPIC_IN_MOV,   "topic_out": TOPIC_OUT_MOV},
    "temperature": {"topic_origin": TOPIC_IN_TEMP,  "topic_out": TOPIC_OUT_TEMP},
    "sound":       {"topic_origin": TOPIC_IN_SOUND,  "topic_out": TOPIC_OUT_SOUND},
}

# =====================================================================
# FILA PARTILHADA E GESTOR DE BACKUPS
# =====================================================================
shared_queue = []
queue_lock = threading.Lock()
queue_condition = threading.Condition(queue_lock)

# Guardar os Resume Tokens para saber onde o MongoDB parou
resume_tokens = {"movements": None, "temperature": None, "sound": None}

backup_manager = BackupManager("script2_backup1.pkl", "script2_backup2.pkl")

# =====================================================================
# CONFIGURAÇÃO DO PUBLICADOR MQTT
# =====================================================================
mqtt_publisher = mqtt.Client(client_id=f"pisid_script2_pub_{GROUP_NUMBER}", clean_session=False)
mqtt_publisher.max_queued_messages_set(0)

def on_connect_publish(client, userdata, flags, rc):
    if rc == 0:
        print(f"[✓ MQTT] Conectado ao Broker LOCAL ({MQTT_BROKER_LOCAL}:{MQTT_PORT_LOCAL})")
        print(f"  Pronto a publicar nos tópicos:")
        print(f"   ↳ {TOPIC_OUT_MOV}")
        print(f"   ↳ {TOPIC_OUT_TEMP}")
        print(f"   ↳ {TOPIC_OUT_SOUND}\n")

mqtt_publisher.on_connect = on_connect_publish

# =====================================================================
# THREAD 1: LER DO MONGODB
# =====================================================================
def mongo_reader_thread(collection_name, topic_origin, topic_out):
    mongo_client_local = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client_local[MONGO_DB_NAME]
    collection = db[collection_name]

    print(f"[*] A monitorizar a coleção '{collection_name}' em tempo real...")

    while True:
        try:
            pipeline = [{"$match": {"operationType": "insert"}}]
            
            kwargs = {}
            # Se houver um Resume Token guardado, começa exatamente desse ponto!
            if resume_tokens.get(collection_name):
                kwargs["resume_after"] = resume_tokens[collection_name]
                print(f"[!] A retomar leitura de '{collection_name}' a partir do último token.")

            with collection.watch(pipeline, **kwargs) as stream:
                for change in stream:
                    token = change["_id"]
                    document = change["fullDocument"]

                    if "_id" in document:
                        del document["_id"]

                    error_type = document.get("ErrorType", -1)

                    if error_type != 0:
                        # Ignorar erro mas guardar o token para não reler
                        with queue_condition:
                            resume_tokens[collection_name] = token
                        continue

                    # Preparar a mensagem
                    document.pop("ErrorType", None)
                    document.pop("status", None)
                    document.pop("error_details", None)

                    msg_to_send = {
                        "topic_out": topic_out,
                        "payload": json.dumps(document, default=str)
                    }

                    # Adicionar à lista partilhada e notificar as outras threads
                    with queue_condition:
                        shared_queue.append(msg_to_send)
                        resume_tokens[collection_name] = token
                        queue_condition.notify()

        except Exception as e:
            print(f"[!] Aviso: Ligação à coleção '{collection_name}' caiu. A reconectar em 3s... (Erro: {e})")
            time.sleep(3)

# =====================================================================
# THREAD 2: FAZER BACKUPS (Conforme o Relatório)
# =====================================================================
def backup_thread():
    while True:
        time.sleep(2)
        with queue_lock:
            # Faz uma cópia da fila e dos tokens para não bloquear muito tempo
            queue_copy = list(shared_queue)
            tokens_copy = dict(resume_tokens)
        
        # O BackupManager guarda a fila e os tokens (o equivalente ao last_id do Script 1)
        backup_manager.save_backup(queue_copy, tokens_copy)

# =====================================================================
# THREAD 3: ENVIAR PARA MQTT E APAGAR DA FILA
# =====================================================================
def mqtt_publisher_thread():
    while True:
        with queue_condition:
            while not shared_queue:
                queue_condition.wait()
            msg = shared_queue.pop(0)

        mqtt_publisher.publish(msg["topic_out"], msg["payload"], qos=2)
        tag = "MOVIMENTOS" if "mov" in msg["topic_out"] else "TEMPERATURA" if "temp" in msg["topic_out"] else "RUÍDO"
        print(f"[→ MQTT] Enviado {tag} para '{msg['topic_out']}' (QoS 2)")

# =====================================================================
# ARRANQUE DO SISTEMA
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  SCRIPT 2, PC1 (MongoDB Change Streams → MQTT Local)")
    print(f"  MongoDB:    {MONGO_URI}")
    print(f"  Broker OUT: {MQTT_BROKER_LOCAL}:{MQTT_PORT_LOCAL}")
    print("=" * 60)
    print()

    # 1. Carregar Estado Anterior
    loaded_queue, loaded_tokens = backup_manager.load_backup()
    if isinstance(loaded_queue, list):
        shared_queue.extend(loaded_queue)
    if isinstance(loaded_tokens, dict) and loaded_tokens != 0:
        resume_tokens.update(loaded_tokens)

    # 2. Ligar MQTT
    mqtt_publisher.connect(MQTT_BROKER_LOCAL, MQTT_PORT_LOCAL, 60)
    mqtt_publisher.loop_start()

    # 3. Iniciar as Threads (3 coleções + backup + publisher)
    threads = []
    
    # 3x Thread 1 (Uma para cada Coleção)
    for coll_name, config in COLLECTIONS_MAP.items():
        t1 = threading.Thread(target=mongo_reader_thread, args=(coll_name, config["topic_origin"], config["topic_out"]), daemon=True)
        threads.append(t1)
        t1.start()

    # Thread 2 (Backup)
    t2 = threading.Thread(target=backup_thread, daemon=True)
    threads.append(t2)
    t2.start()

    # Thread 3 (Publish)
    t3 = threading.Thread(target=mqtt_publisher_thread, daemon=True)
    threads.append(t3)
    t3.start()

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nScript interrompido pelo utilizador. A desligar...")
        mqtt_publisher.loop_stop()
        mqtt_publisher.disconnect()
