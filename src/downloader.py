import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv
import re
import concurrent.futures
import logging
import json
from utils import retry, create_directory

# Cargar configuraciones desde un archivo JSON
def load_config(config_file='config.json'):
    with open(config_file, 'r') as f:
        return json.load(f)

# Cargar configuraciones
config = load_config()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class YupooDownloader:
    def __init__(self, main_url, download_folder):
        self.main_url = main_url
        self.download_folder = download_folder
        self.timeout = config.get('timeout', 10)
        self.max_workers = config.get('max_workers', 20)

    @retry(retries=3, delay=5)
    def create_csv_file(self):
        """
        Crea un archivo CSV con los enlaces de los álbumes en la página principal, con reintentos para manejar errores transitorios.
        """
        page = self._extract_page_number(self.main_url)
        folder = os.path.join(self.download_folder, f"page{page}")
        create_directory(folder)
        file_path = os.path.join(folder, "bf3_strona.csv")
        
        try:
            with requests.Session() as session:
                session.headers.update({"referer": "https://photo.yupoo.com/"})
                response = session.get(self.main_url, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, features="lxml")
                links = [[link.get("href")] for link in soup.find_all("a", class_="album__main")]
                titles = [link.get("title") for link in soup.find_all("a", class_="album__main")]

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["LINKS"])
                writer.writerows(links)
            return titles
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al crear CSV: {e}")
            raise

    def create_file_tests(self, number):
        """
        Crea un archivo CSV con los enlaces de las imágenes del álbum seleccionado.
        Args:
            number (int): Número del álbum en la lista para descargar.
        """
        page = self._extract_page_number(self.main_url)
        folder = os.path.join(self.download_folder, f"page{page}")
        file_path = os.path.join(folder, f"{number}_TESTY.csv")

        df = pd.read_csv(os.path.join(folder, "bf3_strona.csv"), sep=",")
        url = self._get_album_url(number, df)
        soup = self._download_and_parse_html(url)

        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow([number])
            for image_class in [".image__landscape", ".image__portrait"]:
                for x in soup.select(image_class):
                    writer.writerow(["https:" + x["data-src"]])

    def download_photo(self, number, value):
        """
        Descarga las imágenes del álbum especificado.
        Args:
            number (int): Número del álbum en la lista.
            value (str): Título del álbum.
        """
        value = self._change_album_title(value)
        page = self._extract_page_number(self.main_url)
        folder = os.path.join(self.download_folder, f"page{page}", value)
        create_directory(folder)

        df = pd.read_csv(os.path.join(self.download_folder, f"page{page}", f"{number}_TESTY.csv"))
        urls = df.values.flatten().tolist()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_and_save, url, folder, value): url for url in urls if str(url).startswith("http")}
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error al descargar {futures[future]}: {e}")

    def _download_and_save(self, url, folder, title):
        """
        Descarga y guarda la imagen desde una URL.
        Args:
            url (str): URL de la imagen a descargar.
            folder (str): Carpeta donde se guardará la imagen.
            title (str): Título del álbum.
        """
        try:
            with requests.Session() as session:
                session.headers.update({"referer": "https://photo.yupoo.com/"})
                res = session.get(url, timeout=self.timeout)
                res.raise_for_status()

                count = len(os.listdir(folder)) + 1
                image_name = os.path.join(folder, f"{title}_{count}.jpg")
                if not os.path.exists(image_name):
                    with open(image_name, "wb") as f:
                        f.write(res.content)
                    with open(os.path.join(folder, "title.txt"), "w", encoding="utf-8") as f:
                        f.write(title)
        except Exception as e:
            logging.error(f"Error al guardar {url}: {e}")

    def _extract_page_number(self, url):
        """
        Extrae el número de página de la URL proporcionada.
        Args:
            url (str): URL de la página.
        Returns:
            int: Número de página extraído de la URL.
        """
        match = re.search(r'[?&]pag=(\d+)', url)
        if match:
            if '?pag=' in url:
                url = url.replace('?pag=', '&pag=')
            return int(match.group(1))
        raise ValueError("La URL no contiene el parámetro 'pag=n'. Asegúrese de proporcionarlo correctamente.")

    def _get_album_url(self, number, df):
        """
        Obtiene la URL del álbum correspondiente al número especificado.
        Args:
            number (int): Número del álbum en la lista.
            df (DataFrame): DataFrame con los enlaces de los álbumes.
        Returns:
            str: URL completa del álbum.
        """
        text = df["LINKS"][number]
        head, _, tail = self.main_url.partition("x.yupoo.com")
        return head + "x.yupoo.com" + text

    def _download_and_parse_html(self, url):
        """
        Descarga y parsea el HTML de una URL proporcionada.
        Args:
            url (str): URL de la página a parsear.
        Returns:
            BeautifulSoup: Objeto BeautifulSoup con el contenido parseado de la página.
        """
        try:
            with requests.Session() as session:
                session.headers.update({"referer": "https://photo.yupoo.com/"})
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return BeautifulSoup(response.content, "lxml")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error al descargar HTML: {e}")
            raise

    def _change_album_title(self, title):
        """
        Limpia y ajusta el título del álbum para ser usado como nombre de carpeta.
        Args:
            title (str): Título original del álbum.
        Returns:
            str: Título limpio y ajustado.
        """
        #title = re.sub(r'^\d{1,2}\s*', '', title)
        #title = re.sub(r'\bS-XXL\b', '', title)
        #title = title.replace("/", "-")
        title = re.sub(r'[<>:"/\\|?*]', '-', title)
        return title.strip()
