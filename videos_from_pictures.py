import os
from datetime import datetime
from PIL import Image, ImageOps
import numpy as np
from moviepy import ImageSequenceClip
import tkinter as tk
from tkinter import filedialog, messagebox

def find_images(folder_path):
    """
    Находит все изображения в указанной папке и ее подпапках на всех уровнях.
    Выводит информацию о сканировании: количество просмотренных папок, файлов каждого формата и время прошедшее от начала.

    Args:
        folder_path (str): Путь к папке для поиска изображений.

    Returns:
        list: Список путей к найденным изображениям.
    """
    image_files = []
    start_time = datetime.now()
    num_folders_scanned = 0
    format_counts = {}
    for root, dirs, files in os.walk(folder_path):
        num_folders_scanned += 1
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                filepath = os.path.join(root, filename)
                image_files.append(filepath)

                # Считаем количество файлов каждого формата
                file_extension = os.path.splitext(filename)[1].lower()
                if file_extension in format_counts:
                    format_counts[file_extension] += 1
                else:
                    format_counts[file_extension] = 1

        # Обновляем информацию о сканировании
        elapsed_time = (datetime.now() - start_time).total_seconds()
        progress_info = f"Просмотрено папок: {num_folders_scanned}, найдено файлов: {len(image_files)}, время: {elapsed_time:.2f} сек"
        update_progress_label(progress_info)

    return image_files

def update_progress_label(info):
    """
    Обновляет метку прогресса в графическом интерфейсе.
    Args:
        info (str): Информация для отображения.
    """
    progress_label.config(text=info)
    root.update_idletasks()  # Обновляем GUI


def create_video_from_images(folder_path, resolution, extension):
    """
    Создает видеоролик из изображений в указанной папке и ее подпапках, отсортированных по дате создания.
    Изображения масштабируются до указанного разрешения с сохранением пропорций и черным фоном.

    Args:
        folder_path (str): Путь к папке с изображениями.
        resolution (tuple): Разрешение видеоролика (ширина, высота).
        extension (str): Расширение файла для сохранения видеоролика (.mp4, .avi и т.д.).
    """

    image_files = []
    all_image_paths = find_images(folder_path)

    for filepath in all_image_paths:
        try:
            # Получаем дату создания файла (Windows и другие ОС могут возвращать разное время)
            timestamp = os.path.getmtime(filepath)
            date_created = datetime.fromtimestamp(timestamp)
            image_files.append((filepath, date_created))
        except Exception as e:
            print(f"Не удалось обработать файл {filepath}: {e}")

    if not image_files:
        messagebox.showinfo("Внимание", "Изображения не найдены.")
        return

    image_files.sort(key=lambda x: x[1])  # Сортировка по дате создания

    resized_images = []
    try:
        for filepath, _ in image_files:
            img = Image.open(filepath)
            width, height = resolution

            # Вычисляем соотношение сторон изображения
            aspect_ratio = img.width / img.height

            # Вычисляем новые размеры изображения с учетом разрешения и пропорций
            if aspect_ratio > 1:  # Широкое изображение
                new_width = width
                new_height = int(width / aspect_ratio)
            else:  # Высокое изображение
                new_height = height
                new_width = int(height * aspect_ratio)

            # Масштабируем изображение
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Создаем черный фон с размерами разрешения видеоролика
            black_background = Image.new('RGB', resolution, 'black')

            # Вычисляем позицию для вставки изображения на черный фон по центру
            position = ((width - new_width) // 2, (height - new_height) // 2)

            # Вставляем изображение на черный фон
            black_background.paste(img, position)

            resized_images.append(np.array(black_background))  # Преобразуем в numpy array для MoviePy

        clip = ImageSequenceClip(resized_images, fps=2)  # 0.5 секунды на кадр (2 кадра в секунду)

        # Запрашиваем путь для сохранения файла
        save_path = filedialog.asksaveasfilename(defaultextension=extension, filetypes=[("Video files", "*.mp4;*.avi")])
        if not save_path:
            return  # Пользователь отменил сохранение

        clip.write_videofile(save_path, codec="libx264", audio=False)
        messagebox.showinfo("Успех", "Видеоролик успешно создан!")

    except Exception as e:
        print(f"Ошибка при создании видеоролика: {e}")
        messagebox.showerror("Ошибка", f"Ошибка при создании видеоролика:\n{e}")

def browse_folder():
    """Открывает диалоговое окно для выбора папки с изображениями."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path_entry.delete(0, tk.END)
        folder_path_entry.insert(0, folder_selected)

def start_conversion():
    """Запускает процесс конвертации видеоролика."""
    try:
        folder_path = folder_path_entry.get()
        resolution_str = resolution_var.get()
        resolution = tuple(map(int, resolution_str.split('x')))
        extension = extension_var.get()

        if not os.path.isdir(folder_path):
            messagebox.showerror("Ошибка", "Неверный путь к папке.")
            return

        create_video_from_images(folder_path, resolution, extension)

    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат разрешения (например, 1920x1080).")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")

# Создаем графический интерфейс
root = tk.Tk()
root.title("Создание видеоролика из изображений")

# Путь к папке с изображениями
folder_path_label = tk.Label(root, text="Путь к папке:")
folder_path_label.grid(row=0, column=0, padx=5, pady=5)

folder_path_entry = tk.Entry(root, width=50)
folder_path_entry.grid(row=0, column=1, padx=5, pady=5)

browse_button = tk.Button(root, text="Обзор", command=browse_folder)
browse_button.grid(row=0, column=2, padx=5, pady=5)

# Разрешение видеоролика
resolution_label = tk.Label(root, text="Разрешение (ШxВ):")
resolution_label.grid(row=1, column=0, padx=5, pady=5)

resolutions = [
    (320, 240), (640, 480), (854, 480), (1280, 720), (1920, 1080),
    (2048, 1080), (3840, 2160), (4096, 2160)
]

resolution_var = tk.StringVar()
resolution_var.set("3840x2160")  # Значение по умолчанию 4K

resolution_menu = tk.OptionMenu(root, resolution_var, *["{}x{}".format(w, h) for w, h in resolutions])
resolution_menu.grid(row=1, column=1, padx=5, pady=5)
resolutions = [
    (7680, 4320), (3840, 2160), (2560, 1440), (1920, 1080),
    (1280, 720), (854, 480), (640, 360), (426, 240)
]

resolution_var = tk.StringVar()
resolution_var.set("3840x2160")  # Значение по умолчанию 4K

resolution_menu = tk.OptionMenu(root, resolution_var, *["{}x{}".format(w, h) for w, h in resolutions])
resolution_menu.grid(row=1, column=1, padx=5, pady=5)

# Расширение файла
extension_label = tk.Label(root, text="Расширение файла:")
extension_label.grid(row=2, column=0, padx=5, pady=5)

extension_var = tk.StringVar()
extension_var.set(".mp4")  # Значение по умолчанию MP4
extension_menu = tk.OptionMenu(root, extension_var, ".mp4", ".avi", ".mov")
extension_menu.grid(row=2, column=1, padx=5, pady=5)

# Кнопка запуска конвертации
start_button = tk.Button(root, text="Начать конвертацию", command=start_conversion)
start_button.grid(row=3, column=1, padx=5, pady=5)

# Добавляем кнопку "О программе"
about_button = tk.Button(root, text="О программе", command=lambda: messagebox.showinfo("О программе",
    "Программа для создания видеоролика из изображений.\n\n" +
    "Функции:\n1. Выбор папки с изображениями\n2. Установка разрешения выходного видеоролика\n3. Выбор расширения файла\n4. Создание видеоролика\n\n" +
    "Создано по заказу Vladker\nСоздателем: qwen2.5-coder:14b"
))
about_button.grid(row=3, column=0, padx=5, pady=5)

# Добавляем новую метку для отображения информации о прогрессе
progress_label = tk.Label(root, text="")
progress_label.grid(row=4, columnspan=3, padx=5, pady=5)

# Update the mainloop call to the end of the file
root.mainloop()