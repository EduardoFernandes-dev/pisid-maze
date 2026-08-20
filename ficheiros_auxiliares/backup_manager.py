import os
import pickle


class BackupManager:
    def __init__(self, file1="backup1.pkl", file2="backup2.pkl"):
        self.file1 = file1
        self.file2 = file2

    def load_backup(self):
        """
        Retorna um tuple com: (fila_de_mensagens, ultimo_id_processado)
        """
        for file in [self.file1, self.file2]:
            if os.path.exists(file):
                try:
                    with open(file, "rb") as f:
                        data = pickle.load(f)

                    # Compatibilidade: Se for um backup da versão anterior (apenas lista)
                    if isinstance(data, list):
                        print(f"[*] Backup ANTIGO carregado de '{file}' ({len(data)} mensagens). ID de tracking será 0.")
                        return data, 0

                    # Novo formato (Dicionário com a lista e o tracking)
                    elif isinstance(data, dict):
                        queue = data.get("queue", [])
                        last_id = data.get("last_id", 0)
                        print(f"[*] Backup carregado de '{file}': {len(queue)} mensagens. Último ID despachado: {last_id}")
                        return queue, last_id
                except Exception as e:
                    print(f"[!] Erro ao carregar '{file}': {e}. A tentar o próximo backup...")

        print("[*] Nenhum backup válido encontrado. A iniciar estruturas do zero.")
        return [], 0

    def save_backup(self, queue_data, last_id):
        # Agora empacotamos as duas informações num único dicionário
        data_to_save = {"queue": queue_data, "last_id": last_id}
        try:
            with open(self.file1, "wb") as f:
                pickle.dump(data_to_save, f)
            with open(self.file2, "wb") as f:
                pickle.dump(data_to_save, f)
        except Exception as e:
            print(f"[!] Erro crítico ao criar backup: {e}")