import serial
import struct
import threading
import time

# Constantes
SYNC = 0xAA
EXCODE = 0x55

# Definiciones de CÓDIGO de datos
CÓDIGO_BATERÍA = 0x01
CÓDIGO_SEÑAL_DÉBIL = 0x02
CÓDIGO_ATENCIÓN = 0x04
CÓDIGO_MEDITACIÓN = 0x05
CÓDIGO_BRUTO = 0x80
CÓDIGO_EEG_POWER = 0x83

def parse_eeg_power(value):
    if len(value) != 24:
        print("Error: longitud incorrecta para EEG_POWER.")
        return
    
    # Crear una lista para los valores de potencia
    powers = []
    
    # Leer los valores de 3 bytes (sin signo)
    for i in range(0, 24, 3):
        power = int.from_bytes(value[i:i + 3], byteorder='big', signed=False)
        powers.append(power)
    
    # Asignar cada valor a su banda correspondiente
    eeg_power = {
        'delta': powers[0],
        'theta': powers[1],
        'lowAlpha': powers[2],
        'highAlpha': powers[3],
        'lowBeta': powers[4],
        'highBeta': powers[5],
        'lowGamma': powers[6],
        'highGamma': powers[7]
    }
    
    return eeg_power

class ThinkGearStreamParser:
    def __init__(self, handle_data_value_func, name):
        self.handle_data_value_func = handle_data_value_func
        self.buffer = bytearray()
        self.extended_code_level = 0
        self.name = name  # Para identificar la diadema

    def parse_byte(self, byte):
        self.buffer.append(byte)

        if len(self.buffer) >= 2 and self.buffer[0] == SYNC and self.buffer[1] == SYNC:
            if len(self.buffer) >= 3:
                pLength = self.buffer[2]
                if pLength > 169:
                    self.buffer = bytearray()
                    return

                if len(self.buffer) >= 3 + pLength + 1:
                    payload = self.buffer[3:3 + pLength]
                    checksum = self.buffer[3 + pLength]
                    computed_checksum = 0
                    for b in payload:
                        computed_checksum += b
                    computed_checksum = (~computed_checksum) & 0xFF

                    if checksum == computed_checksum:
                        self.parse_payload(payload)
                    self.buffer = bytearray()

    def parse_payload(self, payload):
        index = 0
        while index < len(payload):
            self.extended_code_level = 0
            while index < len(payload) and payload[index] == EXCODE:
                self.extended_code_level += 1
                index += 1
            
            if index >= len(payload):
                break
            
            code = payload[index]
            index += 1
            if code & 0x80:
                length = payload[index]
                index += 1
            else:
                length = 1
            
            if index + length > len(payload):
                break
            
            value = payload[index:index + length]
            index += length

            self.handle_data_value_func(self.extended_code_level, code, length, value, self.name)

def handle_data_value_func(extended_code_level, code, value_length, value, name):
    if extended_code_level == 0:
        if code == CÓDIGO_SEÑAL_DÉBIL:
            print(f"[{name}] Nivel de señal débil: {value[0] & 0xFF}")
        elif code == CÓDIGO_ATENCIÓN:
            print(f"[{name}] Nivel de atención: {value[0] & 0xFF}")
        elif code == CÓDIGO_MEDITACIÓN:
            print(f"[{name}] Nivel de meditación: {value[0] & 0xFF}")
        elif code == CÓDIGO_BATERÍA:
            print(f"[{name}] Nivel de batería: {value[0] & 0xFF}")
        #elif code == CÓDIGO_EEG_POWER:
            eeg_power = parse_eeg_power(value)
            if eeg_power:
                print(f"[{name}] EEG Power Levels:")
                print(f"  Delta: {eeg_power['delta']}")
                print(f"  Theta: {eeg_power['theta']}")
                print(f"  Low Alpha: {eeg_power['lowAlpha']}")
                print(f"  High Alpha: {eeg_power['highAlpha']}")
                print(f"  Low Beta: {eeg_power['lowBeta']}")
                print(f"  High Beta: {eeg_power['highBeta']}")
                print(f"  Low Gamma: {eeg_power['lowGamma']}")
                print(f"  High Gamma: {eeg_power['highGamma']}")

def read_from_port(port, name):
    parser = ThinkGearStreamParser(handle_data_value_func, name)
    try:
        ser = serial.Serial(port, baudrate=9600, timeout=1)
        print(f"[{name}] Conectado exitosamente en {port}")
        
        while True:
            byte = ser.read(1)
            if byte:
                parser.parse_byte(ord(byte))
    
    except KeyboardInterrupt:
        print(f"\n[{name}] Interrupción del teclado recibida. Cerrando...")
    
    except serial.SerialException as e:
        print(f"\n[{name}] Error en la comunicación serial: {e}")
    
    finally:
        if ser.is_open:
            ser.close()
            print(f"[{name}] Puerto serie cerrado.")

def main():
    # Primero conectar la diadema 1
    thread1 = threading.Thread(target=read_from_port, args=('COM3', 'Diadema 1'))
    thread1.start()
    
    # Esperar unos segundos para asegurarnos de que la primera diadema se conecte
    #time.sleep(3)  # Ajusta este tiempo si es necesario

    # Luego conectar la diadema 2
    #thread2 = threading.Thread(target=read_from_port, args=('COM3', 'Diadema 2'))
    #thread2.start()

    # Ambos hilos trabajan al mismo tiempo sin necesidad de join()

if __name__ == "__main__":
    main()
