Simulador de Cajeros Bancarios Concurrentes (ATM-Concurrency)

Este proyecto es una simulación web multi-usuario diseñada para demostrar el problema de la Condición de Carrera en la programación concurrente y cómo el uso de un Mutex (Exclusión Mutua) garantiza la integridad de los datos en un recurso compartido (el saldo de una cuenta bancaria).

El backend está desarrollado con Python y Flask, y es accesible a través de una red local, permitiendo que varios dispositivos actúen como "cajeros" concurrentes.

Requisitos de Instalación

Asegúrate de tener instalado lo siguiente en tu sistema:

Python 3.x: (Recomendado Python 3.8 o superior).

pip: El administrador de paquetes de Python (generalmente viene con Python).

Configuración del Entorno

Sigue estos pasos para preparar y ejecutar el backend de la aplicación:

1. Clonar y Navegar

Asumo que el código (app.py y la carpeta static/index.html) se encuentra dentro de un directorio llamado Banco/src/.

# Navega al directorio raíz del proyecto
cd Banco/


2. Crear y Activar el Entorno Virtual

Es fundamental usar un entorno virtual (venv) para aislar las dependencias del proyecto de tu sistema global.

# Crear el entorno virtual (solo la primera vez)
python3 -m venv .venv 

# Activar el entorno virtual (requerido cada vez que trabajes en el proyecto)
source .venv/bin/activate  # macOS / Linux
# o
.\.venv\Scripts\activate   # Windows (PowerShell/CMD)


3. Instalar Dependencias

Solo necesitas instalar el framework Flask.

# Instalar Flask
pip install Flask


Ejecución y Acceso

1. Iniciar el Servidor Flask

Ejecuta la aplicación. El código está configurado para escuchar en el puerto 5001 y en todas las interfaces de red (0.0.0.0), permitiendo el acceso local y remoto (LAN).

# Asegúrate de estar con el entorno virtual activado
python app.py


El servidor debería indicar que está corriendo en http://0.0.0.0:5001.

2. Acceso Local para Otros Dispositivos (LAN)

Para que otros dispositivos (teléfonos, tablets, otras laptops) puedan simular a los cajeros, deben acceder a la IP de tu computadora.

Encontrar tu IP Local:

Si usaste ifconfig: Tu IP es 192.168.3.44.

URL de Acceso: Proporciona a tus compañeros esta dirección: http://192.168.3.44:5001.

Configuración del Firewall (¡Importante!):

Si otros dispositivos no pueden acceder, tu Firewall está bloqueando el puerto 5001.

Debes añadir una Regla de Entrada que permita las conexiones TCP en el puerto 5001 a través de tu red privada/doméstica.

Cajero Global (Estrés)

Cómo Demostrar la Condición de Carrera
