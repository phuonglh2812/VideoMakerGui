import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
import threading
import os
from video_processor import VideoProcessor
from subtitle_settings import SubtitlePresetManager, SubtitleSettings
from font_utils import get_system_fonts

class VideoProcessorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Video Processor")
        self.geometry("1000x800")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Style configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.hook_mp3_path = None
        self.audio_mp3_path = None
        self.hook_srt_path = None
        self.audio_srt_path = None
        self.thumbnail_path = None
        self.video_folder_path = None
        
        # System fonts
        self.system_fonts = get_system_fonts()
        
        # Subtitle settings
        self.font_var = ctk.StringVar(value="Arial")
        self.font_size_var = ctk.StringVar(value="48")
        self.primary_color_var = ctk.StringVar(value="&HFFFFFF&")
        self.outline_color_var = ctk.StringVar(value="&H000000&")
        self.back_color_var = ctk.StringVar(value="&H000000&")
        self.outline_var = ctk.StringVar(value="2")
        self.shadow_var = ctk.StringVar(value="0")
        self.margin_v_var = ctk.StringVar(value="20")
        self.margin_h_var = ctk.StringVar(value="20")
        self.alignment_var = ctk.StringVar(value="2")
        self.max_chars_var = ctk.StringVar(value="40")
        
        # Preset manager
        self.preset_manager = SubtitlePresetManager()
        self.current_preset_var = ctk.StringVar(value="Default")
        
        # Create processor instance
        self.processor = VideoProcessor(os.getcwd())
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Video Processor",
            font=("Helvetica", 24, "bold")
        )
        self.title_label.grid(row=0, column=0, pady=20)
        
        # File selection frames
        self.create_file_selector("Hook Audio (MP3/WAV, Optional)", "hook_mp3", 1)
        self.create_file_selector("Main Audio (MP3/WAV)", "audio_mp3", 2)
        self.create_file_selector("Hook SRT (Optional)", "hook_srt", 3)
        self.create_file_selector("Audio SRT", "audio_srt", 4)
        self.create_file_selector("Thumbnail PNG (Optional)", "thumbnail", 5)
        self.create_folder_selector("Video Folder", "video_folder", 6)
        
        # Subtitle Settings Frame
        self.create_subtitle_settings_frame()
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.grid(row=8, column=0, padx=20, pady=10, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self.progress_frame)
        self.progress.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.progress.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready",
            font=("Helvetica", 12)
        )
        self.status_label.grid(row=1, column=0, pady=5)
        
        # Process button
        self.process_button = ctk.CTkButton(
            self.main_frame,
            text="Process Video",
            command=self.process_video,
            font=("Helvetica", 14, "bold"),
            height=40
        )
        self.process_button.grid(row=9, column=0, pady=20)

    def create_subtitle_settings_frame(self):
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Presets
        preset_frame = ctk.CTkFrame(settings_frame)
        preset_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        preset_label = ctk.CTkLabel(preset_frame, text="Preset:")
        preset_label.grid(row=0, column=0, padx=5)
        
        preset_menu = ctk.CTkOptionMenu(
            preset_frame,
            variable=self.current_preset_var,
            values=self.preset_manager.get_preset_names(),
            command=self.load_preset
        )
        preset_menu.grid(row=0, column=1, padx=5)
        
        save_preset_button = ctk.CTkButton(
            preset_frame,
            text="Save As New",
            command=self.save_preset
        )
        save_preset_button.grid(row=0, column=2, padx=5)
        
        delete_preset_button = ctk.CTkButton(
            preset_frame,
            text="Delete",
            command=self.delete_preset
        )
        delete_preset_button.grid(row=0, column=3, padx=5)
        
        # Font settings
        row = 1
        
        # Font dropdown
        label = ctk.CTkLabel(settings_frame, text="Font:")
        label.grid(row=row, column=0, padx=5, pady=2)
        
        font_menu = ctk.CTkOptionMenu(
            settings_frame,
            variable=self.font_var,
            values=self.system_fonts,
            dynamic_resizing=False,
            width=300
        )
        font_menu.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        row += 1
        
        # Font size
        self.create_setting_entry(settings_frame, "Font Size:", self.font_size_var, row)
        row += 1
        
        # Colors with color picker buttons
        self.create_color_setting(settings_frame, "Primary Color:", self.primary_color_var, row)
        row += 1
        self.create_color_setting(settings_frame, "Outline Color:", self.outline_color_var, row)
        row += 1
        self.create_color_setting(settings_frame, "Back Color:", self.back_color_var, row)
        row += 1
        
        self.create_setting_entry(settings_frame, "Outline:", self.outline_var, row)
        row += 1
        self.create_setting_entry(settings_frame, "Shadow:", self.shadow_var, row)
        row += 1
        self.create_setting_entry(settings_frame, "Vertical Margin:", self.margin_v_var, row)
        row += 1
        self.create_setting_entry(settings_frame, "Horizontal Margin:", self.margin_h_var, row)
        row += 1
        
        # Alignment dropdown
        label = ctk.CTkLabel(settings_frame, text="Alignment:")
        label.grid(row=row, column=0, padx=5, pady=2)
        
        alignment_menu = ctk.CTkOptionMenu(
            settings_frame,
            variable=self.alignment_var,
            values=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
            dynamic_resizing=False
        )
        alignment_menu.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        row += 1
        
        self.create_setting_entry(settings_frame, "Max Characters:", self.max_chars_var, row)

    def create_color_setting(self, parent, label_text, variable, row):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=2)
        
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        
        entry = ctk.CTkEntry(frame, textvariable=variable)
        entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        def pick_color():
            color = colorchooser.askcolor(title=f"Choose {label_text}")
            if color[0]:  # color is ((R, G, B), #RRGGBB)
                r, g, b = [int(x) for x in color[0]]
                # Convert RGB to ASS format &HBBGGRR&
                ass_color = f"&H{b:02X}{g:02X}{r:02X}&"
                variable.set(ass_color)
        
        color_button = ctk.CTkButton(
            frame,
            text="Pick",
            command=pick_color,
            width=60
        )
        color_button.grid(row=0, column=1)

    def create_setting_entry(self, parent, label_text, variable, row):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=2)
        
        entry = ctk.CTkEntry(parent, textvariable=variable)
        entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")

    def load_preset(self, preset_name=None):
        if preset_name is None:
            preset_name = self.current_preset_var.get()
        
        preset = self.preset_manager.get_preset(preset_name)
        if preset:
            self.font_var.set(preset.font)
            self.font_size_var.set(preset.font_size)
            self.primary_color_var.set(preset.primary_color)
            self.outline_color_var.set(preset.outline_color)
            self.back_color_var.set(preset.back_color)
            self.outline_var.set(preset.outline)
            self.shadow_var.set(preset.shadow)
            self.margin_v_var.set(preset.margin_v)
            self.margin_h_var.set(preset.margin_h)
            self.alignment_var.set(preset.alignment)
            self.max_chars_var.set(preset.max_chars)

    def save_preset(self):
        dialog = ctk.CTkInputDialog(
            text="Enter preset name:",
            title="Save Preset"
        )
        preset_name = dialog.get_input()
        if preset_name:
            settings = SubtitleSettings(
                name=preset_name,
                font=self.font_var.get(),
                font_size=self.font_size_var.get(),
                primary_color=self.primary_color_var.get(),
                outline_color=self.outline_color_var.get(),
                back_color=self.back_color_var.get(),
                outline=self.outline_var.get(),
                shadow=self.shadow_var.get(),
                margin_v=self.margin_v_var.get(),
                margin_h=self.margin_h_var.get(),
                alignment=self.alignment_var.get(),
                max_chars=self.max_chars_var.get()
            )
            self.preset_manager.add_preset(settings)
            self.update_preset_menu()

    def delete_preset(self):
        preset_name = self.current_preset_var.get()
        if preset_name == "Default":
            messagebox.showerror("Error", "Cannot delete the Default preset!")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete preset '{preset_name}'?"):
            self.preset_manager.delete_preset(preset_name)
            self.current_preset_var.set("Default")
            self.load_preset("Default")
            self.update_preset_menu()

    def update_preset_menu(self):
        preset_names = self.preset_manager.get_preset_names()
        menu = self.main_frame.winfo_children()[7].winfo_children()[0].winfo_children()[1]
        menu.configure(values=preset_names)

    def create_file_selector(self, label_text, attr_name, row):
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(frame, text=label_text, width=150)
        label.grid(row=0, column=0, padx=5)
        
        path_var = ctk.StringVar()
        path_entry = ctk.CTkEntry(frame, textvariable=path_var)
        path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        button = ctk.CTkButton(
            frame,
            text="Browse",
            width=100,
            command=lambda: self.browse_file(attr_name, path_var)
        )
        button.grid(row=0, column=2, padx=5)
        
        setattr(self, f"{attr_name}_var", path_var)

    def create_folder_selector(self, label_text, attr_name, row):
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(frame, text=label_text, width=150)
        label.grid(row=0, column=0, padx=5)
        
        path_var = ctk.StringVar()
        path_entry = ctk.CTkEntry(frame, textvariable=path_var)
        path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        button = ctk.CTkButton(
            frame,
            text="Browse",
            width=100,
            command=lambda: self.browse_folder(attr_name, path_var)
        )
        button.grid(row=0, column=2, padx=5)
        
        setattr(self, f"{attr_name}_var", path_var)

    def browse_file(self, attr_name, path_var):
        filetypes = {
            'hook_mp3': [('Audio files', '*.mp3;*.wav'), ('MP3 files', '*.mp3'), ('WAV files', '*.wav')],
            'audio_mp3': [('Audio files', '*.mp3;*.wav'), ('MP3 files', '*.mp3'), ('WAV files', '*.wav')],
            'hook_srt': [('SRT files', '*.srt')],
            'audio_srt': [('SRT files', '*.srt')],
            'thumbnail': [('PNG files', '*.png')]
        }
        
        filename = filedialog.askopenfilename(
            title=f'Select {attr_name}',
            filetypes=filetypes.get(attr_name, [('All files', '*.*')])
        )
        
        if filename:
            path_var.set(filename)
            setattr(self, attr_name + '_path', filename)

    def browse_folder(self, attr_name, path_var):
        folder = filedialog.askdirectory(title=f'Select {attr_name}')
        if folder:
            path_var.set(folder)
            setattr(self, attr_name + '_path', folder)

    def update_progress(self, status, progress):
        self.status_label.configure(text=status)
        self.progress.set(progress / 100)
        self.update()

    def process_video(self):
        if not self.audio_mp3_path:
            messagebox.showerror("Error", "Audio MP3 is required!")
            return
        
        if not self.video_folder_path:
            messagebox.showerror("Error", "Video folder is required!")
            return
                
        # Disable process button
        self.process_button.configure(state="disabled")
        
        # Start processing in a new thread
        def process_thread():
            try:
                settings = SubtitleSettings(
                    font=self.font_var.get(),
                    font_size=self.font_size_var.get(),
                    primary_color=self.primary_color_var.get(),
                    outline_color=self.outline_color_var.get(),
                    back_color=self.back_color_var.get(),
                    outline=self.outline_var.get(),
                    shadow=self.shadow_var.get(),
                    margin_v=self.margin_v_var.get(),
                    margin_h=self.margin_h_var.get(),
                    alignment=self.alignment_var.get(),
                    max_chars=self.max_chars_var.get()
                )
                output = self.processor.process_video(
                    hook_mp3=self.hook_mp3_path,
                    audio_mp3=self.audio_mp3_path,
                    hook_srt=self.hook_srt_path,
                    audio_srt=self.audio_srt_path,
                    thumbnail=self.thumbnail_path,
                    video_folder=self.video_folder_path,
                    subtitle_settings=settings,
                    callback=self.update_progress
                )
                self.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Video processed successfully!\nOutput: {output}"
                ))
            except Exception as error:
                error_msg = str(error)
                self.after(0, lambda: messagebox.showerror("Error", error_msg))
            finally:
                self.after(0, lambda: self.process_button.configure(state="normal"))
        
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()

def main():
    app = VideoProcessorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()