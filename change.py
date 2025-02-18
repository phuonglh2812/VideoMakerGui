import os
import tkinter as tk
from tkinter import filedialog, messagebox

def convert_text_to_txt(folder_path):
    if not os.path.isdir(folder_path):
        messagebox.showerror("Lỗi", "Thư mục không hợp lệ!")
        return
    
    count = 0
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".text"):
            old_path = os.path.join(folder_path, file_name)
            new_path = os.path.join(folder_path, file_name.replace(".text", ".txt"))
            os.rename(old_path, new_path)
            count += 1

    messagebox.showinfo("Hoàn thành", f"Đã chuyển đổi {count} file .text sang .txt")

# ================== GUI với Tkinter ==================
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        convert_text_to_txt(folder)

# Tạo giao diện
root = tk.Tk()
root.title("Chuyển đổi .text -> .txt")
root.geometry("400x200")

label = tk.Label(root, text="Chọn thư mục chứa file .text:")
label.pack(pady=10)

btn_select = tk.Button(root, text="Chọn thư mục", command=select_folder)
btn_select.pack(pady=5)

root.mainloop()
