# Yupoo Downloader

Yupoo Downloader es una herramienta que permite automatizar la descarga de imágenes desde catálogos de Yupoo. Con esta aplicación, puedes descargar todos los álbumes e imágenes de una URL específica de Yupoo, de manera eficiente y con una interfaz gráfica amigable.

## Características
- Descarga automatizada de imágenes de catálogos de Yupoo.
- Interfaz gráfica amigable para facilitar la configuración y la descarga.
- Control de progreso de la descarga con barra de progreso y temporizador.
- Reintento automático en caso de errores de red.

## Requisitos
- Python 3.6+
- Dependencias listadas en `requirements.txt`.

## Instalación
1. Clona este repositorio:
   ```sh
   git clone https://github.com/tuusuario/yupoo-downloader.git
   ```
2. Navega al directorio del proyecto:
   ```sh
   cd yupoo-downloader
   ```
3. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
4. Instala el paquete:
   ```sh
   pip install .
   ```

## Uso
Puedes ejecutar la aplicación desde la línea de comandos utilizando el siguiente comando:
```sh
yupoo-downloader
```

También puedes ejecutar directamente el script de la GUI:
```sh
python src/yupoo_downloader/gui.py
```

## Configuración
En la interfaz gráfica, deberás proporcionar:
- **URL de Yupoo**: La URL del catálogo que deseas descargar. Asegúrate de que la URL contiene el parámetro `?page=n` o `&page=n`.
- **Carpeta de Descarga**: La carpeta local donde se guardarán las imágenes descargadas.

## Estructura del Proyecto
- **setup.py**: Archivo para instalar el proyecto como un paquete.
- **requirements.txt**: Define las dependencias necesarias.
- **README.md**: Descripción del proyecto y guía de uso.
- **src/yupoo_downloader/**: Contiene el código fuente dividido en varios módulos:
  - `downloader.py`: Lógica para la descarga de imágenes.
  - `gui.py`: Interfaz gráfica de usuario.
  - `utils.py`: Funciones auxiliares como la creación de directorios y reintentos automáticos.

## Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request si deseas mejorar el proyecto.

## Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.