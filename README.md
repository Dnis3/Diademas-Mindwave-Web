# Proyecto: Plataforma web de monitoreo multiusuario de actividad cerebral en tiempo real mediante diademas MindWave Mobile.

Este proyecto utiliza Flask para crear una aplicación web que permite conectar, desconectar y monitorear los datos de dos diademas MindWave a través de puertos COM, este proyecto está abierto a mejoras y se pueden adaptar múltiples diademas si así se requiere. Los datos recolectados incluyen métricas como atención, meditación y potencias EEG de diferentes bandas, que se guardan en archivos CSV descargables y se presentan a través de una interfaz web.

## Características

- **Conexión simultánea de dos diademas MindWave:** La aplicación permite conectar dos dispositivos a través de diferentes puertos COM.
- **Almacenamiento en CSV:** Los datos recolectados de las diademas se almacenan periódicamente en archivos CSV, incluyendo una marca de tiempo. 
- **Normalización de datos EEG:** Los valores de las bandas EEG se normalizan en un rango de 0 a 100 para facilitar su análisis.
- **Interfaz web:**
  - Conexión y desconexión de las diademas.
  - Descarga de archivos CSV con los datos recolectados.
  - Visualización en tiempo real del estado y los datos de las diademas.
- **Endpoints JSON:** Permite exponer los datos recolectados mediante una API REST.

## Requisitos

- **Python:** 3.7 o superior
- **Librerías necesarias:**
  - `Flask`
  - `pyserial`
  - `struct`
  - `csv`
  - `threading`
- **Hardware:**
  - Dos diademas MindWave.
  - Puertos COM configurados adecuadamente.

## Instalación

1. Clona este repositorio en tu máquina local:

   ```bash
   git clone https://github.com/tu-usuario/proyecto-diademas.git
   cd proyecto-diademas

2. Instala las dependencias necesarias:
   
   ```bash
   pip install flask pyserial

4. Configura los puertos COM en el archivo principal:
   
   - Actualiza la función `get_port(name)` con los puertos asignados a tus diademas.
   - O si lo prefieres sigue las instrucciones que se encuentran en `/help`

## Uso
  1. **Inicia la aplicación Flask:**

  ```bash
  python app.py 
  ```
  
  2. Abre tu navegador y ve a http://127.0.0.1:5000.

  3. Ve a la seccion `\diademas`

  4. Conecta las diademas y visualiza los datos

## Funcionalidades disponibles:

  - Página principal: Brinda una bienvenida al usuario y el menú principal (Acceso a la interfaz de monitoreo y ayuda).
  - Visualización de datos en tiempo real.
  - Conectar/Desconectar diademas: Usa los botones correspondientes en la interfaz.
  - Descargar datos CSV: Haz clic en los enlaces de descarga para obtener los archivos con datos recolectados.
  
## Archivos importantes
  `app.py`: Código principal de la aplicación.
  `diadema1.csv` y `diadema2.csv`: Archivos CSV donde se almacenan los datos recolectados.
  `templates/index.html`: Página principal de la aplicación.
  `templates/diademas.html`: Interfaz para gestionar las diademas.
  `templates/help.html`: Página de ayuda.

## Notas adicionales
  - **Reintentos automáticos:** Si la conexión a una diadema falla, el sistema intentará reconectar cada 5 segundos.
  - **Normalización de valores:** Los valores de las bandas EEG se normalizan con base en máximos predefinidos, que pueden ajustarse según sea necesario.
  - **Documentación oficial:** Este proyecto fue desarrollado con base en la documentación oficial de Neurosky. Puedes encontrarla en https://developer.neurosky.com/docs/doku.php?id=thinkgear_communications_protocol#thinkgear_data_values 




