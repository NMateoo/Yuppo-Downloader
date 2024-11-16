import os
import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
from tkinter import ttk
from threading import Thread, Event
import time
import logging
import json
from PIL import Image, ImageTk
from downloader import YupooDownloader
import sys
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = "config.json"

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=(None, 10))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

class YupooGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yupoo Downloader Optimizado")
        self.load_config()
        self.create_panels()
        self.downloader = None
        self.is_downloading = False
        self.stop_event = Event()
        self.pause_event = Event()
        self.pause_event.set()
        self.is_paused = False
        self.elapsed_time = 0
        self.downloaded_albums = []  # Almacena los álbumes descargados

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as file:
                self.config = json.load(file)
        except FileNotFoundError:
            self.config = {
                "timeout": 15, 
                "max_workers": 10, 
                "bg_color": "#FFFFFF", 
                "font_size": 10, 
                "text_color": "#000000", 
                "button_color": "#DDDDDD", 
                "button_text_color": "#000000", 
                "button_width": 15, 
                "button_height": 2
            }
        
    def save_config(self):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(self.config, file, indent=4)

    def create_panels(self):
        self.root.configure(bg=self.config.get("bg_color", "#FFFFFF"))
        font_size = self.config.get("font_size", 10)
        text_color = self.config.get("text_color", "#000000")
        button_color = self.config.get("button_color", "#DDDDDD")
        button_text_color = self.config.get("button_text_color", "#000000")
        button_width = self.config.get("button_width", 15)
        button_height = self.config.get("button_height", 2)

        # Menu
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Ajustes", command=self.open_settings)
        menubar.add_cascade(label="Opciones", menu=settings_menu)
        menubar.add_cascade(label="Ayuda", command=self.show_help)
        self.root.config(menu=menubar)

        # Panel de Configuración
        config_frame = tk.LabelFrame(self.root, text="Configuración", padx=10, pady=10, bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color)
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        self.url_label = tk.Label(config_frame, text="URL de Yupoo (con ?page=n o &page=n):", bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color, font=(None, font_size))
        self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.url_entry = tk.Entry(config_frame, width=50, font=(None, font_size))
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        self.folder_label = tk.Label(config_frame, text="Carpeta de Descarga:", bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color, font=(None, font_size))
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.folder_entry = tk.Entry(config_frame, width=50, font=(None, font_size))
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)

        self.select_folder_button = tk.Button(config_frame, text="Seleccionar Carpeta", command=self.select_folder, font=(None, font_size), bg=button_color, fg=button_text_color, width=button_width, height=button_height)
        self.select_folder_button.grid(row=2, column=0, padx=5, pady=5)

        self.modify_url_var = tk.BooleanVar()
        self.modify_url_checkbox = tk.Checkbutton(config_frame, text="Modificar URL (?pag= a &pag=)", variable=self.modify_url_var, bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color, font=(None, font_size))
        self.modify_url_checkbox.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        ToolTip(self.select_folder_button, "")

        ToolTip(self.modify_url_checkbox, "Si contiene el simbolo '?' puede descargar mas fotos de la cuenta por problemas dentro del Yuppo.\n Marca esta opción si solo quieres que descargue las fotos que aparecen en el albúm.")


        # Panel de Control
        control_frame = tk.LabelFrame(self.root, text="Controles", padx=10, pady=10, bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color)
        control_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.start_button = tk.Button(control_frame, text="Iniciar Descarga", command=self.start_download, font=(None, font_size), bg=button_color, fg=button_text_color, width=button_width, height=button_height)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(control_frame, text="Detener Descarga", command=self.stop_download, state=tk.DISABLED, font=(None, font_size), bg=button_color, fg=button_text_color, width=button_width, height=button_height)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        self.resume_button = tk.Button(control_frame, text="Pausar Descarga", command=self.toggle_pause, state=tk.DISABLED, font=(None, font_size), bg=button_color, fg=button_text_color, width=button_width, height=button_height)
        self.resume_button.grid(row=0, column=2, padx=5, pady=5)

        # Panel de Progreso
        progress_frame = tk.LabelFrame(self.root, text="Progreso", padx=10, pady=10, bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color)
        progress_frame.grid(row=0, column=2, padx=10, pady=10, sticky='nsew')

        self.progressbar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
        self.progressbar.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        
        self.label_progress = tk.Label(progress_frame, text="Progreso: 0%", bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color, font=(None, font_size))
        self.label_progress.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='w')

        self.timer_label = tk.Label(progress_frame, text="Tiempo Total: 0 s", bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color, font=(None, font_size))
        self.timer_label.grid(row=2, column=0, columnspan=1, pady=5, sticky='w')

        self.album_label = tk.Label(progress_frame, text="Progreso del Álbum: 0 de 0", bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color, font=(None, font_size))
        self.album_label.grid(row=2, column=1, columnspan=2, pady=5, sticky='w')

        # Panel de Productos Descargados
        products_frame = tk.LabelFrame(self.root, text="Productos Descargados", padx=10, pady=10, bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color)
        products_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.products_listbox = tk.Listbox(products_frame, width=100, height=10, font=(None, font_size))
        self.products_listbox.grid(row=0, column=0, padx=5, pady=5)
        self.products_listbox.bind('<<ListboxSelect>>', self.display_album_photos)

        # Panel de Log
        log_frame = tk.LabelFrame(self.root, text="Registro de Actividades", padx=10, pady=10, bg=self.config.get("bg_color", "#FFFFFF"), fg=text_color)
        log_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

        self.log_area = tk.Text(log_frame, width=100, height=10, state='normal', font=(None, font_size))
        self.log_area.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

        # Botón de Cerrar
        close_button = tk.Button(self.root, text="Cerrar", command=self.root.quit, font=(None, font_size), bg=button_color, fg=button_text_color, width=button_width, height=button_height)
        close_button.grid(row=3, column=1, padx=10, pady=10)

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ajustes")

        # Timeout setting
        timeout_label = tk.Label(settings_window, text="Timeout (segundos):")
        timeout_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')
        timeout_entry = tk.Entry(settings_window)
        timeout_entry.insert(0, str(self.config.get("timeout", 15)))
        timeout_entry.grid(row=0, column=1, padx=10, pady=10)

        # Max workers setting
        max_workers_label = tk.Label(settings_window, text="Max Workers:")
        max_workers_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')
        max_workers_entry = tk.Entry(settings_window)
        max_workers_entry.insert(0, str(self.config.get("max_workers", 10)))
        max_workers_entry.grid(row=1, column=1, padx=10, pady=10)

        # Background color setting
        color_label = tk.Label(settings_window, text="Color de Fondo:")
        color_label.grid(row=2, column=0, padx=10, pady=10, sticky='w')
        color_button = tk.Button(settings_window, text="Seleccionar Color", command=lambda: self.choose_color(color_button))
        color_button.grid(row=2, column=1, padx=10, pady=10)

        # Text color setting
        text_color_label = tk.Label(settings_window, text="Color de Texto:")
        text_color_label.grid(row=3, column=0, padx=10, pady=10, sticky='w')
        text_color_button = tk.Button(settings_window, text="Seleccionar Color", command=lambda: self.choose_color_generic("text_color", text_color_button))
        text_color_button.grid(row=3, column=1, padx=10, pady=10)

        # Button color setting
        button_color_label = tk.Label(settings_window, text="Color de Botones:")
        button_color_label.grid(row=4, column=0, padx=10, pady=10, sticky='w')
        button_color_button = tk.Button(settings_window, text="Seleccionar Color", command=lambda: self.choose_color_generic("button_color", button_color_button))
        button_color_button.grid(row=4, column=1, padx=10, pady=10)

        # Button text color setting
        button_text_color_label = tk.Label(settings_window, text="Color de Texto de Botones:")
        button_text_color_label.grid(row=5, column=0, padx=10, pady=10, sticky='w')
        button_text_color_button = tk.Button(settings_window, text="Seleccionar Color", command=lambda: self.choose_color_generic("button_text_color", button_text_color_button))
        button_text_color_button.grid(row=5, column=1, padx=10, pady=10)

        # Font size setting
        font_size_label = tk.Label(settings_window, text="Tamaño de Fuente:")
        font_size_label.grid(row=6, column=0, padx=10, pady=10, sticky='w')
        font_size_entry = tk.Entry(settings_window)
        font_size_entry.insert(0, str(self.config.get("font_size", 10)))
        font_size_entry.grid(row=6, column=1, padx=10, pady=10)

        # Button width setting
        button_width_label = tk.Label(settings_window, text="Ancho de Botón:")
        button_width_label.grid(row=7, column=0, padx=10, pady=10, sticky='w')
        button_width_entry = tk.Entry(settings_window)
        button_width_entry.insert(0, str(self.config.get("button_width", 15)))
        button_width_entry.grid(row=7, column=1, padx=10, pady=10)

        # Button height setting
        button_height_label = tk.Label(settings_window, text="Altura de Botón:")
        button_height_label.grid(row=8, column=0, padx=10, pady=10, sticky='w')
        button_height_entry = tk.Entry(settings_window)
        button_height_entry.insert(0, str(self.config.get("button_height", 2)))
        button_height_entry.grid(row=8, column=1, padx=10, pady=10)

        # Reset button
        reset_button = tk.Button(settings_window, text="Restablecer Valores", command=self.reset_settings)
        reset_button.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

        # Save button
        save_button = tk.Button(settings_window, text="Guardar", command=lambda: self.save_settings(timeout_entry, max_workers_entry, font_size_entry, button_width_entry, button_height_entry))
        save_button.grid(row=10, column=0, columnspan=2, padx=10, pady=10)

    def choose_color(self, button):
        color_code = colorchooser.askcolor(title="Seleccione un color")[1]
        if color_code:
            self.config["bg_color"] = color_code
            button.configure(bg=color_code)

    def choose_color_generic(self, config_key, button):
        color_code = colorchooser.askcolor(title="Seleccione un color")[1]
        if color_code:
            self.config[config_key] = color_code
            button.configure(bg=color_code)

    def reset_settings(self):
        self.config = {
            "timeout": 15, 
            "max_workers": 10, 
            "bg_color": "#FFFFFF", 
            "font_size": 8, 
            "text_color": "#000000", 
            "button_color": "#DDDDDD", 
            "button_text_color": "#000000", 
            "button_width": 15, 
            "button_height": 2
        }
        self.save_config()
        messagebox.showinfo("Restablecido", "Los ajustes han sido restablecidos a sus valores predeterminados. La aplicación se reiniciará para aplicar los cambios.")
        self.root.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def save_settings(self, timeout_entry, max_workers_entry, font_size_entry, button_width_entry, button_height_entry):
        try:
            self.config["timeout"] = int(timeout_entry.get())
            self.config["max_workers"] = int(max_workers_entry.get())
            self.config["font_size"] = int(font_size_entry.get())
            self.config["button_width"] = int(button_width_entry.get())
            self.config["button_height"] = int(button_height_entry.get())
            self.save_config()
            messagebox.showinfo("Guardado", "Los ajustes han sido guardados con éxito. La aplicación se reiniciará para aplicar los cambios.")
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese valores válidos para los ajustes.")

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Ayuda")
        help_text = (
            "Instrucciones para usar el programa:\n"
            "1. Ingrese la URL de Yupoo que contenga el parámetro 'page=n'.\n"
            "2. Seleccione la carpeta donde desea guardar las descargas.\n"
            "3. Haga clic en 'Iniciar Descarga' para comenzar la descarga.\n"
            "4. Puede pausar o detener la descarga usando los botones correspondientes.\n"
            "5. Use el botón 'Cerrar' para salir del programa."
        )
        help_label = tk.Label(help_window, text=help_text, justify='left')
        help_label.pack(padx=10, pady=10)

    def start_download(self):
        url = self.url_entry.get()
        download_folder = self.folder_entry.get()

        if self.modify_url_var.get():
            if '?pag=' in url:
                url = url.replace('?pag=', '&pag=')

        if not url or ('pag=' not in url):
            messagebox.showerror("Error", "Por favor, ingrese una URL válida que contenga el parámetro 'pag=n'.")
            return

        if not download_folder or not os.path.exists(download_folder):
            messagebox.showerror("Error", "Por favor, seleccione una carpeta de descarga válida.")
            return

        self.url_entry.config(state=tk.DISABLED)
        self.folder_entry.config(state=tk.DISABLED)
        self.select_folder_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.NORMAL)
        self.is_downloading = True
        self.stop_event.clear()
        self.pause_event.set()
        self.is_paused = False

        self.downloader = YupooDownloader(main_url=url, download_folder=download_folder)
        download_thread = Thread(target=self.run_download)
        download_thread.start()

        self.start_time = time.time() - self.elapsed_time
        self.timer_thread = Thread(target=self.update_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def update_timer(self):
        while self.is_downloading:
            if self.stop_event.is_set():
                break
            if not self.is_paused:
                self.elapsed_time = int(time.time() - self.start_time)
                self.timer_label.config(text=f"Tiempo Total: {self.elapsed_time} s")
            time.sleep(1)

    def run_download(self):
        try:
            title_list = self.downloader.create_csv_file()
            self.total_albums = len(title_list)
            self.progressbar['maximum'] = self.total_albums

            for index, value in enumerate(title_list):
                if self.stop_event.is_set():
                    break
                self.pause_event.wait()
                self.update_progress(index + 1, self.total_albums)
                self.album_label.config(text=f"Progreso del Álbum: {index + 1} de {self.total_albums}")
                self.log_area.insert(tk.END, f"Procesando álbum: {value}\n")
                self.log_area.yview(tk.END)
                
                self.downloader.create_file_tests(index)
                self.downloader.download_photo(index, value)
                
                # Añadir álbum descargado a la lista de productos
                self.downloaded_albums.append(value)
                self.products_listbox.insert(tk.END, value)
                
            if not self.stop_event.is_set():
                messagebox.showinfo("Éxito", "Descarga completada con éxito.")
        except Exception as e:
            logging.error(f"Error durante la descarga: {e}")
            messagebox.showerror("Error", f"Error durante la descarga: {e}")
        finally:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.DISABLED)
            self.url_entry.config(state=tk.NORMAL)
            self.folder_entry.config(state=tk.NORMAL)
            self.select_folder_button.config(state=tk.NORMAL)
            self.is_downloading = False

    def stop_download(self):
        self.stop_event.set()
        self.pause_event.set()
        self.is_downloading = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.url_entry.config(state=tk.NORMAL)
        self.folder_entry.config(state=tk.NORMAL)
        self.select_folder_button.config(state=tk.NORMAL)
        self.elapsed_time = int(time.time() - self.start_time)
        messagebox.showinfo("Descarga Detenida", "La descarga ha sido detenida.")

    def toggle_pause(self):
        if self.is_paused:
            self.pause_event.set()
            self.resume_button.config(text="Pausar Descarga")
            self.stop_button.config(state=tk.NORMAL)
            self.start_time = time.time() - self.elapsed_time
            self.log_area.insert(tk.END, "Descarga reanudada\n")
            self.log_area.yview(tk.END)
        else:
            self.pause_event.clear()
            self.resume_button.config(text="Reanudar Descarga")
            self.stop_button.config(state=tk.DISABLED)
            self.elapsed_time = int(time.time() - self.start_time)
            self.log_area.insert(tk.END, "Descarga pausada\n")
            self.log_area.yview(tk.END)
        self.is_paused = not self.is_paused

    def display_album_photos(self, event):
        # Obtener el álbum seleccionado
        selection = event.widget.curselection()
        if selection:
            album_index = selection[0]
            album_name = self.downloaded_albums[album_index]
            album_name_normalized = re.sub(r'[\\/:*?"<>|]', '-', album_name)  # Normalizar nombre de carpeta eliminando caracteres inválidos
            album_folder = os.path.join(os.path.normpath(self.folder_entry.get()), "page1", album_name_normalized)

            print(album_name + ' ', album_name_normalized + ' ', album_folder + ' ')

            if os.path.exists(album_folder):
                photos = [f for f in os.listdir(album_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

                if photos:
                    photo_window = tk.Toplevel(self.root)
                    photo_window.title(f"Fotos de {album_name}")

                    row = 0
                    col = 0
                    for photo in photos:
                        photo_path = os.path.join(album_folder, photo)
                        img = Image.open(photo_path)
                        img = img.resize((200, 200))
                        img = ImageTk.PhotoImage(img)

                        img_label = tk.Label(photo_window, image=img)
                        img_label.image = img  # Mantener una referencia para evitar el recolector de basura
                        img_label.grid(row=row, column=col, padx=5, pady=5)
                        img_label.bind("<Button-1>", lambda e, photo_path=photo_path: self.show_large_photo(photo_path))

                        col += 1
                        if col >= 4:
                            col = 0
                            row += 1
                else:
                    messagebox.showinfo("Sin Fotos", f"No se encontraron fotos en el álbum: {album_name}")
            else:
                messagebox.showerror("Error", f"No se encontró la carpeta del álbum: {album_name}")

    def update_progress(self, current, total):
        progress = int((current / total) * 100)
        self.progressbar['value'] = current
        self.label_progress.config(text=f"Progreso: {progress}%")

    def show_large_photo(self, photo_path):
        # Abrir una ventana para mostrar la imagen en grande
        large_photo_window = tk.Toplevel(self.root)
        large_photo_window.title("Imagen Grande")

        img = Image.open(photo_path)
        img = img.resize((400, 400))
        img = ImageTk.PhotoImage(img)

        img_label = tk.Label(large_photo_window, image=img)
        img_label.image = img  # Mantener una referencia para evitar el recolector de basura
        img_label.pack(padx=10, pady=10)

if __name__ == "__main__":
    def main():
        root = tk.Tk()
        app = YupooGUI(root)
        root.mainloop()
    main()
