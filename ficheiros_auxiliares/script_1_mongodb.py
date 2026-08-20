import os
import json
import re
import time
import threading
import warnings
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Importar a classe de gestão de backups
from backup_manager import BackupManager
from validacoes import DataValidator
from config import (
    GROUP_NUMBER, MQTT_BROKER_PUBLIC, MQTT_PORT_PUBLIC,
    MONGO_URI, MONGO_DB_NAME,
    TOPIC_IN_MOV, TOPIC_IN_TEMP, TOPIC_IN_SOUND,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================================
# CONFIGURAÇÃO MONGODB (Replica Set no PC1)
# =============================================================================

# Timeout de 2 segundos para falhar rápido e não congelar a consola
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
db = mongo_client[MONGO_DB_NAME]

# --- Instâncias e Variáveis Globais ---
os.makedirs("./ficheiros_auxiliares/backups", exist_ok=True)
backupManager = BackupManager(file1="./ficheiros_auxiliares/backups/backup_s1_1.pkl",
                              file2="./ficheiros_auxiliares/backups/backup_s1_2.pkl")

# Instanciar o validador a partir do novo ficheiro
validator = DataValidator()

# Fila de espera na memória RAM
message_queue = []

# --- threading.Condition + threading.Event (Sem Espera Ativa) ---
queue_condition = threading.Condition()
backup_event = threading.Event()

next_incoming_id = 1
last_processed_id = 0


# --- Função Utilitária ---
def fix_json_payload(payload_str):
    fixed_str = re.sub(r'([a-zA-Z0-9_]+):', r'"\1":', payload_str)
    return fixed_str.replace("'", '"')


# --- THREADS 1, 2 e 3: Produtores (Receber MQTT do Broker PÚBLICO) ---
def mqtt_subscriber_thread(topic):
    """Subscreve ao broker PÚBLICO para receber dados do Mazerun."""
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(topic, qos=1)
            print(f"[MQTT IN] À escuta do tópico: {topic} (QoS 1)")

    def on_message(client, userdata, msg):
        global next_incoming_id
        raw_payload = msg.payload.decode("utf-8")

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            try:
                payload = json.loads(fix_json_payload(raw_payload))
            except:
                return

        # Coloca a mensagem na fila e acorda as outras threads instantaneamente
        with queue_condition:
            message_queue.append({"msg_id": next_incoming_id, "topic": msg.topic, "payload": payload})
            print(f"[FILA] Recebido MQTT ({msg.topic}): {payload}")
            next_incoming_id += 1

            queue_condition.notify()  # Acorda o Consumidor!
            backup_event.set()        # Acorda o Backup!

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER_PUBLIC, MQTT_PORT_PUBLIC, 60)
    client.loop_forever()


# --- THREAD 4: Backup de Segurança (Event-Driven) ---
def backup_thread():
    while True:
        # Fica a dormir SEM gastar CPU até que alguém chame backup_event.set()
        backup_event.wait()
        backup_event.clear()  # Limpa o sinal para voltar a dormir na próxima ronda

        with queue_condition:
            queue_copy = list(message_queue)
            current_last_id = last_processed_id

        backupManager.save_backup(queue_copy, current_last_id)


# --- THREAD 5: Consumidor (Validar → MongoDB com ErrorType) ---
def consumer_thread():
    global last_processed_id

    print("[BD] A aguardar mensagens na fila para validar e guardar no MongoDB...")

    while True:
        msg_item = None

        # Bloqueia até que haja mensagens na fila (sem polling/sleep)
        with queue_condition:
            while len(message_queue) == 0:
                queue_condition.wait()

            msg_item = message_queue[0]

        if msg_item:
            msg_id = msg_item.get("msg_id", 0)
            topic = msg_item["topic"]
            payload = msg_item["payload"]
            tag = "MOVIMENTOS" if "mov" in topic else "TEMPERATURA" if "temp" in topic else "RUÍDO"

            if 0 < msg_id <= last_processed_id:
                print(f"[*] AVISO: Mensagem {msg_id} já processada em sessão anterior. A descartar da fila...")
                with queue_condition:
                    message_queue.pop(0)
                    backup_event.set()
                continue

            try:
                # === PASSO 1: VALIDAR OS DADOS ===
                status, error_details = validator.validate(topic, payload)

                # Criar cópia do payload para não alterar o original na fila
                doc_to_store = dict(payload)

                # === PASSO 2: ADICIONAR ErrorType ===
                if status == "outlier":
                    doc_to_store["ErrorType"] = 1
                elif status == "spam":
                    doc_to_store["ErrorType"] = 2
                elif status == "invalid":
                    doc_to_store["ErrorType"] = 3
                else:
                    doc_to_store["ErrorType"] = 0

                doc_to_store["status"] = status
                if error_details:
                    doc_to_store["error_details"] = error_details

                # === PASSO 3: GUARDAR NO MONGODB ===
                try:
                    if topic == TOPIC_IN_MOV:
                        db["movements"].insert_one(doc_to_store)
                    elif topic == TOPIC_IN_TEMP:
                        db["temperature"].insert_one(doc_to_store)
                    elif topic == TOPIC_IN_SOUND:
                        db["sound"].insert_one(doc_to_store)
                except DuplicateKeyError:
                    print(f"[-] A mensagem {msg_id} já existia no MongoDB. A ignorar duplicação...")

                primary_node = mongo_client.primary
                primary_port = primary_node[1] if primary_node else "Desconhecida"

                # Feedback visual
                if status == "ok":
                    print(f"\n[✓ {tag}] VÁLIDO - Guardado na BD MongoDB (PRIMARY na porta {primary_port}) (ID: {msg_id})")
                elif status == "invalid":
                    print(f"\n[✗ {tag}] INVÁLIDO - Guardado na BD com aviso | ID: {msg_id} | {error_details}")
                elif status == "outlier":
                    print(f"\n[⚠ {tag}] OUTLIER - Guardado na BD com aviso | ID: {msg_id} | {error_details}")
                elif status == "spam":
                    print(f"\n[⚠ {tag}] SPAM - Guardado na BD com aviso | ID: {msg_id} | {error_details}")

                # Resumo periódico de estatísticas
                total = validator.ok_count + validator.invalid_count + validator.outlier_count + validator.spam_count
                if total > 0 and total % 20 == 0:
                    print(f"\n{'=' * 55}")
                    print(f"  ESTATÍSTICAS: {validator.ok_count} válidos | "
                          f"{validator.invalid_count} inválidos | "
                          f"{validator.outlier_count} outliers | "
                          f"{validator.spam_count} spam")
                    print(f"{'=' * 55}")

                # === PASSO 4: ATUALIZAR TRACKING E APAGAR DA FILA ===
                with queue_condition:
                    last_processed_id = msg_id
                    message_queue.pop(0)
                    backup_event.set()  # Notifica o backup que a fila mudou

            except Exception as e:
                print(f"[!] AVISO: Falha ao ligar à BD para guardar a msg {msg_id}. A aguardar 2s... Erro: {e}")
                time.sleep(2)


# --- Arranque do Sistema ---
if __name__ == "__main__":
    print("=" * 55)
    print("  SCRIPT 1, PC1 (Validador + MongoDB)")
    print(f"  Broker IN:  {MQTT_BROKER_PUBLIC}:{MQTT_PORT_PUBLIC}")
    print(f"  Saída:      MongoDB ({MONGO_DB_NAME})")
    print("=" * 55)

    message_queue, last_processed_id = backupManager.load_backup()

    if not message_queue and last_processed_id == 0:
        print("[*] Arranque a zeros detetado. A limpar as coleções no MongoDB para evitar conflitos...")
        for i in range(15):
            try:
                db["movements"].delete_many({})
                db["temperature"].delete_many({})
                db["sound"].delete_many({})
                print("[*] Base de dados limpa com sucesso!")
                break
            except Exception as e:
                print(f"[!] MongoDB ainda não elegeu um PRIMARY (tentativa {i+1}/15). A aguardar 2s...")
                time.sleep(2)
        else:
            print("[!] AVISO CRÍTICO: Falha ao limpar a base de dados após 30 segundos. O script vai continuar, mas podem existir dados antigos!")

    if message_queue:
        max_id_in_queue = max([m.get("msg_id", 0) for m in message_queue] + [0])
        next_incoming_id = max(max_id_in_queue, last_processed_id) + 1

    topics = [TOPIC_IN_MOV, TOPIC_IN_TEMP, TOPIC_IN_SOUND]
    threads = []

    for t in topics:
        thread = threading.Thread(target=mqtt_subscriber_thread, args=(t,), daemon=True)
        threads.append(thread)
        thread.start()

    t_backup = threading.Thread(target=backup_thread, daemon=True)
    threads.append(t_backup)
    t_backup.start()

    t_consumer = threading.Thread(target=consumer_thread, daemon=True)
    threads.append(t_consumer)
    t_consumer.start()

    try:
        # Event.wait() bloqueia para sempre a Main Thread sem gastar recursos
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nScript interrompido pelo utilizador. A desligar de forma segura...")
        mongo_client.close()
