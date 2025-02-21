#Importación de librerías
from flask import Flask, render_template, jsonify
import serial
import os
import threading
import time
import csv  # Importación para manejar archivos CSV
from flask import send_file

#Llamada a la función principal
app = Flask(__name__)

# Constantes
SYNC = 0xAA
EXCODE = 0x55

# Definiciones de CÓDIGO de datos
CÓDIGO_BATERÍA = 0x01
CÓDIGO_SEÑAL_DÉBIL = 0x02
CÓDIGO_ATENCIÓN = 0x04
CÓDIGO_MEDITACIÓN = 0x05
CÓDIGO_EEG_POWER = 0x83

# Datos globales para almacenar la información de las diademas
diadema_data = {
    'Diadema 1': {'status': 'Desconectado'},
    'Diadema 2': {'status': 'Desconectado'},
    'Diadema 3': {'status': 'Desconectado'}  # Agregada la tercera diadema
}

# Función para inicializar el archivo CSV y escribir el encabezado
def init_csv(file_name):
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Escribir los encabezados
        writer.writerow(['timestamp', 'diadema', 'signal_strength', 'attention', 'meditation',
                         'delta', 'theta', 'lowAlpha', 'highAlpha', 'lowBeta', 'highBeta', 
                         'lowGamma', 'highGamma'])

# Función para guardar los datos en el archivo CSV
def save_to_csv(file_name, name, data):
    with open(file_name, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Obtener la marca de tiempo
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        
        # Escribir una nueva fila con los datos que se obtienen de las diademas
        writer.writerow([
            timestamp,
            name,
            data.get('signal_strength', ''),
            data.get('attention', ''),
            data.get('meditation', ''),
            data.get('eeg_power', {}).get('delta', ''),
            data.get('eeg_power', {}).get('theta', ''),
            data.get('eeg_power', {}).get('lowAlpha', ''),
            data.get('eeg_power', {}).get('highAlpha', ''),
            data.get('eeg_power', {}).get('lowBeta', ''),
            data.get('eeg_power', {}).get('highBeta', ''),
            data.get('eeg_power', {}).get('lowGamma', ''),
            data.get('eeg_power', {}).get('highGamma', '')
        ])

# Inicializa los archivos CSV para las tres diademas
csv_file_diadema_1 = 'diadema1.csv'
csv_file_diadema_2 = 'diadema2.csv'
csv_file_diadema_3 = 'diadema3.csv'  # Agregado archivo CSV para la tercera diadema

init_csv(csv_file_diadema_1)
init_csv(csv_file_diadema_2)
init_csv(csv_file_diadema_3)  # Inicializar CSV para la tercera diadema

#Lectura de los valores egg
def parse_eeg_power(value):
    #Lee el tamaño del paquete
    if len(value) != 24:
        print("Error: longitud incorrecta para EEG_POWER.")
        return
    
    #Se crea un array donde se almacenan los valores para porteriormente normalizaarlos (datos crudos)
    powers = []
    for i in range(0, 24, 3):
        power = int.from_bytes(value[i:i + 3], byteorder='big', signed=False)
        powers.append(power)
    
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

# Máximos conocidos para normalización
max_values = {
    'delta': 3826920,
    'theta': 2073192,
    'lowAlpha': 1182188,
    'highAlpha': 1242286,
    'lowBeta': 1248142,
    'highBeta': 1407590,
    'lowGamma': 971627,
    'highGamma': 817668
}

#Función que normaliza los valores
def normalize_value(value, max_value):
    return (value / max_value) * 100 if max_value > 0 else 0

#Clase principal en donde se leen los datos de la diadema
class ThinkGearStreamParser:
    def __init__(self, handle_data_value_func, name):
        self.handle_data_value_func = handle_data_value_func
        self.buffer = bytearray()
        self.extended_code_level = 0
        self.name = name

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

#Función que identifica el código de datos que se está obteniendo 
def handle_data_value_func(extended_code_level, code, value_length, value, name):
    global diadema_data
    if extended_code_level == 0:
        if code == CÓDIGO_SEÑAL_DÉBIL:
            diadema_data[name]['signal_strength'] = value[0] & 0xFF
        elif code == CÓDIGO_ATENCIÓN:
            diadema_data[name]['attention'] = value[0] & 0xFF
        elif code == CÓDIGO_MEDITACIÓN:
            diadema_data[name]['meditation'] = value[0] & 0xFF
        elif code == CÓDIGO_BATERÍA:
            diadema_data[name]['battery'] = value[0] & 0xFF
        elif code == CÓDIGO_EEG_POWER:
            eeg_power = parse_eeg_power(value)
            # Normalizar los valores de EEG y convertir a int
            for key in max_values.keys():
                if key in eeg_power:
                    eeg_power[key] = int(normalize_value(eeg_power[key], max_values[key]))
            diadema_data[name]['eeg_power'] = eeg_power

#Funcion para conectar las diademas a los puertos específicos
def read_from_port(port, name):
    global diadema_data
    parser = ThinkGearStreamParser(handle_data_value_func, name)
    
    while diadema_data[name]['status'] == 'Conectando':
        try:
            with serial.Serial(port, baudrate=9600, timeout=1) as ser:
                print(f"[{name}] Conectado al puerto {port}")
                diadema_data[name]['status'] = 'Conectado'
                
                while diadema_data[name]['status'] == 'Conectado':
                    byte = ser.read(1)
                    if byte:
                        parser.parse_byte(ord(byte))
        
        except (serial.SerialException, OSError) as e:
            print(f"\n[{name}] Error en la comunicación serial: {e}")
            diadema_data[name]['status'] = 'Desconectado'
        
        print(f"[{name}] Intentando reconectar en 5 segundos...")
        time.sleep(5)

# Hilo para guardar datos cada segundo
def save_data_periodically():
    while True:
        time.sleep(1)  # Guardar los datos cada segundo
        # Guardar los datos de las tres diademas en sus respectivos archivos CSV
        if diadema_data['Diadema 1']['status'] == 'Conectado':
            save_to_csv(csv_file_diadema_1, 'Diadema 1', diadema_data['Diadema 1'])
        if diadema_data['Diadema 2']['status'] == 'Conectado':
            save_to_csv(csv_file_diadema_2, 'Diadema 2', diadema_data['Diadema 2'])
        if diadema_data['Diadema 3']['status'] == 'Conectado':  # Agregado guardado de datos para la tercera diadema
            save_to_csv(csv_file_diadema_3, 'Diadema 3', diadema_data['Diadema 3'])

#Rutas para redireccionar en el css
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/diademas')
def diademas():
    return render_template('diademas.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/data')
def data():
    return jsonify(diadema_data)

@app.route('/connect/<name>', methods=['POST'])
def connect(name):
    if name in diadema_data and diadema_data[name]['status'] == 'Desconectado':
        diadema_data[name]['status'] = 'Conectando'
        thread = threading.Thread(target=read_from_port, args=(get_port(name), name))
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'Conectando'})
    return jsonify({'status': 'Error', 'message': 'Diadema no encontrada o ya conectada'})

@app.route('/disconnect/<name>', methods=['POST'])
def disconnect(name):
    if name in diadema_data:
        diadema_data[name]['status'] = 'Desconectado'
        return jsonify({'status': 'Desconectado'})
    return jsonify({'status': 'Error', 'message': 'Diadema no encontrada'})

@app.route('/download/<diadema_name>')
def download(diadema_name):
    if diadema_name == 'diadema1':
        return send_file(csv_file_diadema_1, as_attachment=True)
    elif diadema_name == 'diadema2':
        return send_file(csv_file_diadema_2, as_attachment=True)
    elif diadema_name == 'diadema3':  # Agregada descarga para la tercera diadema
        return send_file(csv_file_diadema_3, as_attachment=True)
    return "Diadema no encontrada", 404

def get_port(name):
    if name == 'Diadema 1':
        return 'COM8'
    elif name == 'Diadema 2':
        return 'COM3'
    elif name == 'Diadema 3':  # Agregado puerto para la tercera diadema
        return 'COM4'  # Asegúrate de cambiar esto al puerto correcto
    return None

if __name__ == '__main__':
    # Iniciar hilo para guardar datos periódicamente
    threading.Thread(target=save_data_periodically, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))