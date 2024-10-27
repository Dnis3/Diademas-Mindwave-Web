#Para ver si los puertos com estan disponibles se debe poner el comando "mode com8" en el cmd
import serial.tools.list_ports

def listar_puertos():
    puertos = serial.tools.list_ports.comports()
    for puerto in puertos:
        print(f"Puerto: {puerto.device}, Descripción: {puerto.description}")

listar_puertos()
