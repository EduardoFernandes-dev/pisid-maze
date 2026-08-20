import os
import statistics
from datetime import datetime, timedelta
from collections import deque

from config import (
    GROUP_NUMBER_INT,
    ZSCORE_THRESHOLD,
    SLIDING_WINDOW_SIZE,
    FUTURE_TOLERANCE_SECONDS,
)


class DataValidator:
    """
    Valida mensagens do MAZERUN e deteta outliers.
    Mantém janelas deslizantes em memória para cálculos de Z-Score.
    Guarda o histórico num ficheiro CSV para facilitar a análise de outliers e falsos positivos.
    Implementa um sistema de tolerância elástica (Data Drift) ajustando o Desvio Padrão.
    Deteta mensagens duplicadas (compara apenas com a ÚLTIMA mensagem de cada tópico).
    """

    def __init__(self):
        # Janelas deslizantes para deteção de outliers (últimos 5 valores)
        self._temp_window = deque(maxlen=SLIDING_WINDOW_SIZE)
        self._sound_window = deque(maxlen=SLIDING_WINDOW_SIZE)

        # Dicionário para guardar a última mensagem de cada tópico (deteção de spam)
        self._last_message_per_topic = {}

        # Contadores de erros seguidos por sensor (Para tolerância dinâmica)
        self._outlier_streaks = {
            "Temperature": 0,
            "Sound": 0
        }

        # Contadores Globais
        self.invalid_count = 0
        self.outlier_count = 0
        self.spam_count = 0
        self.ok_count = 0

        # Configuração do ficheiro de Log (CSV)
        self.log_dir = "./ficheiros_auxiliares/logs"
        self.log_file = os.path.join(self.log_dir, "analise_outliers.csv")
        os.makedirs(self.log_dir, exist_ok=True)

    @property
    def total_errors(self):
        """Número total de entradas erradas + outliers filtrados + duplicados."""
        return self.invalid_count + self.outlier_count + self.spam_count

    # --- API Pública ---
    def validate(self, topic, payload):
        # Passo 1: Validação comum a todos os tipos
        status, reason = self._validate_common(payload)
        if status == "invalid":
            self.invalid_count += 1
            return status, reason

        # Passo 1.5: Validação de Duplicados (Compara só com a última desse tópico)
        is_spam, dup_reason = self._check_spam(topic, payload)
        if is_spam:
            self.spam_count += 1
            return "spam", dup_reason

        # Passo 2: Validação específica por tipo
        if "mov" in topic:
            status, reason = self._validate_movement(payload)
        elif "temp" in topic:
            status, reason = self._validate_temperature(payload)
        elif "sound" in topic:
            status, reason = self._validate_sound(payload)
        else:
            self.invalid_count += 1
            return "invalid", f"Tipo de tópico desconhecido: {topic}"

        if status == "invalid":
            self.invalid_count += 1
            return status, reason

        # Passo 3: Deteção de outliers (apenas para temp/sound que passaram validação)
        if "temp" in topic:
            status, reason = self._check_outlier(
                payload["Temperature"], self._temp_window, "Temperature"
            )
        elif "sound" in topic:
            status, reason = self._check_outlier(
                payload["Sound"], self._sound_window, "Sound"
            )

        if status == "outlier":
            self.outlier_count += 1
        else:
            self.ok_count += 1

        return status, reason

    # --- Validação de Duplicados ---
    def _check_spam(self, topic, payload):
        """Verifica se a mensagem atual é exatamente igual à última mensagem processada naquele tópico."""
        try:
            # Converter o payload num tuplo ordenado e imutável de strings para poder comparar de forma fiável
            payload_signature = tuple(sorted((str(k), str(v)) for k, v in payload.items()))

            if self._last_message_per_topic.get(topic) == payload_signature:
                return True, f"Mensagem duplicada (igual à última do tópico {topic})"

            # Se for diferente, atualiza o dicionário com esta nova mensagem para futuras comparações
            self._last_message_per_topic[topic] = payload_signature
            return False, None
        except Exception:
            # Em caso de erro na geração da assinatura ignora a verificação
            return False, None

    # --- Validação Comum ---
    def _validate_common(self, payload):
        if not isinstance(payload, dict):
            return "invalid", "Payload não é um dicionário"

        player = payload.get("Player")
        if player is None:
            return "invalid", "Campo 'Player' em falta"

        try:
            player_int = int(player)
        except (ValueError, TypeError):
            return "invalid", f"Player não é um inteiro válido: {player}"

        if player_int != GROUP_NUMBER_INT:
            return "invalid", f"Player é {player_int}, esperado {GROUP_NUMBER_INT}"

        return "ok", None

    # --- Validação de Movimentos ---
    def _validate_movement(self, payload):
        required = ["Marsami", "RoomOrigin", "RoomDestiny", "Status"]
        for field in required:
            if field not in payload:
                return "invalid", f"Campo obrigatório em falta: {field}"
            try:
                int(payload[field])
            except (ValueError, TypeError):
                return "invalid", f"Campo '{field}' não é um inteiro válido: {payload[field]}"

        marsami = int(payload["Marsami"])
        room_origin = int(payload["RoomOrigin"])
        room_destiny = int(payload["RoomDestiny"])
        status = int(payload["Status"])

        if marsami <= 0:
            return "invalid", f"Marsami deve ser > 0, recebido {marsami}"
        if room_origin < 0:
            return "invalid", f"RoomOrigin deve ser >= 0, recebido {room_origin}"
        if room_destiny < 0:
            return "invalid", f"RoomDestiny deve ser >= 0, recebido {room_destiny}"
        if status not in (0, 1, 2):
            return "invalid", f"Status deve ser 0, 1 ou 2, recebido {status}"

        return "ok", None

    # --- Validação de Temperatura ---
    def _validate_temperature(self, payload):
        required = ["Hour", "Temperature"]
        for field in required:
            if field not in payload:
                return "invalid", f"Campo obrigatório em falta: {field}"

        status, reason = self._validate_hour(payload["Hour"])
        if status == "invalid": return status, reason

        temp = payload["Temperature"]
        if not isinstance(temp, (int, float)):
            try:
                float(temp)
            except (ValueError, TypeError):
                return "invalid", f"Temperature não é numérico: {temp}"

        return "ok", None

    # --- Validação de Som ---
    def _validate_sound(self, payload):
        required = ["Hour", "Sound"]
        for field in required:
            if field not in payload:
                return "invalid", f"Campo obrigatório em falta: {field}"

        status, reason = self._validate_hour(payload["Hour"])
        if status == "invalid": return status, reason

        sound = payload["Sound"]
        if not isinstance(sound, (int, float)):
            try:
                float(sound)
            except (ValueError, TypeError):
                return "invalid", f"Sound não é numérico: {sound}"

        return "ok", None

    # --- Validação de Data/Hora ---
    def _validate_hour(self, hour_str):
        if not isinstance(hour_str, str): return "invalid", f"Hour não é uma string: {hour_str}"
        parsed_dt = None
        formats = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                parsed_dt = datetime.strptime(hour_str, fmt)
                break
            except ValueError:
                continue

        if parsed_dt is None: return "invalid", f"Hour tem formato inválido: {hour_str}"
        now = datetime.now()
        if parsed_dt.date() != now.date(): return "invalid", f"Hour não é de hoje: {hour_str}"
        if parsed_dt > now + timedelta(seconds=FUTURE_TOLERANCE_SECONDS): return "invalid", f"Hour está no futuro: {hour_str}"
        return "ok", None

    # --- Sistema de Logging para CSV ---
    def _log_to_csv(self, sensor, value, status, mean="", stdev="", zscore="", streak="", reason=""):
        """Escreve uma linha no ficheiro CSV para análise futura."""
        file_exists = os.path.isfile(self.log_file)

        reason_clean = reason.replace(",", ";") if reason else "Ok"
        dt_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        with open(self.log_file, mode="a", encoding="utf-8") as f:
            if not file_exists:
                # Adicionei a coluna Tolerancia(Streak) para veres o aumento ao vivo no Excel
                f.write("HoraLocal,Sensor,Valor,Decisao,MediaJanela,StdevAjustado,ZScore,Tolerancia(Streak),Detalhes\n")

            m_str = f"{mean:.4f}" if isinstance(mean, float) else mean
            s_str = f"{stdev:.4f}" if isinstance(stdev, float) else stdev
            z_str = f"{zscore:.4f}" if isinstance(zscore, float) else zscore

            f.write(f"{dt_str},{sensor},{value},{status},{m_str},{s_str},{z_str},{streak},{reason_clean}\n")

    # --- Deteção de Outliers (Z-Score Tolerante a Shifts) ---
    def _check_outlier(self, value, values_list, sensor_name):
        value = float(value)

        # Dados insuficientes, aceitar e adicionar à janela
        if len(values_list) < SLIDING_WINDOW_SIZE:
            values_list.append(value)
            self._log_to_csv(sensor_name, value, "Válido", streak=self._outlier_streaks[sensor_name], reason="A preencher janela inicial")
            return "ok", None

        # Calcular Estatísticas Base
        mean = statistics.mean(values_list)
        stdev_original = statistics.stdev(values_list)

        # === A TUA FÓRMULA DE ELASTICIDADE ===
        num_outliers = self._outlier_streaks[sensor_name]
        adjusted_stdev = stdev_original * (1 + (1 / SLIDING_WINDOW_SIZE) * num_outliers)

        # Se desvio padrão ajustado é 0, todos os valores são rigorosamente iguais
        if adjusted_stdev == 0:
            if value != mean:
                if abs(value - mean) > abs(mean) * 0.5:
                    self._outlier_streaks[sensor_name] += 1
                    reason = f"{sensor_name} outlier: valor={value}, média={mean:.4f}, stdev=0, diferença={abs(value - mean):.4f}"
                    self._log_to_csv(sensor_name, value, "OUTLIER", mean, adjusted_stdev, "", self._outlier_streaks[sensor_name], reason)
                    return "outlier", reason

            # Valor válido (é igual à média)
            self._outlier_streaks[sensor_name] = max(0, self._outlier_streaks[sensor_name] - 1)
            values_list.append(value)
            self._log_to_csv(sensor_name, value, "Válido", mean, adjusted_stdev, 0.0, self._outlier_streaks[sensor_name])
            return "ok", None

        # Cálculo do Z-Score com o Limiar Expandido
        z_score = (value - mean) / adjusted_stdev

        if abs(z_score) > ZSCORE_THRESHOLD:
            self._outlier_streaks[sensor_name] += 1  # Penaliza: Aumenta a tolerância para a próxima
            reason = f"{sensor_name} outlier: valor={value}, média={mean:.4f}, stdev_ajust={adjusted_stdev:.4f}, Z-Score={z_score:.2f} (limite=±{ZSCORE_THRESHOLD})"
            self._log_to_csv(sensor_name, value, "OUTLIER", mean, adjusted_stdev, z_score, self._outlier_streaks[sensor_name], reason)
            return "outlier", reason

        # Não é outlier, adicionar à janela e diminuir penalização
        self._outlier_streaks[sensor_name] = max(0, self._outlier_streaks[sensor_name] - 1)  # Recompensa: Diminui a tolerância
        values_list.append(value)
        self._log_to_csv(sensor_name, value, "Válido", mean, adjusted_stdev, z_score, self._outlier_streaks[sensor_name])
        return "ok", None

    # --- Reset (para novas simulações) ---
    def reset(self):
        """Reinicia todas as janelas e contadores."""
        self._temp_window.clear()
        self._sound_window.clear()
        self._last_message_per_topic.clear()
        self._outlier_streaks = {"Temperature": 0, "Sound": 0}

        self.invalid_count = 0
        self.outlier_count = 0
        self.spam_count = 0
        self.ok_count = 0

        # Opcional: Apagar ficheiro de log antigo ao fazer reset
        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except:
                pass