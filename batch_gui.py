import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from video_processor import VideoProcessor
from batch_settings import BatchSettings
import shutil

class BatchProcessorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Set window title and theme
        self.title("Batch Video Processor")
        self.geometry("800x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Load settings
        self.batch_settings = BatchSettings()
        
        # Create work directory
        self.work_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(self.work_dir, exist_ok=True)
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Input folder
        input_row = ctk.CTkFrame(self.main_frame)
        input_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(input_row, text="Input Folder:").pack(side="left")
        self.batch_input = ctk.CTkEntry(input_row)
        self.batch_input.pack(side="left", fill="x", expand=True, padx=5)
        self.batch_input.insert(0, self.batch_settings.settings["input_folder"])
        
        browse_btn = ctk.CTkButton(input_row, text="Browse", command=self.select_batch_input)
        browse_btn.pack(side="right")
        
        # Output folder
        output_row = ctk.CTkFrame(self.main_frame)
        output_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(output_row, text="Output Folder:").pack(side="left")
        self.batch_output = ctk.CTkEntry(output_row)
        self.batch_output.pack(side="left", fill="x", expand=True, padx=5)
        self.batch_output.insert(0, self.batch_settings.settings["output_folder"])
        
        browse_btn = ctk.CTkButton(output_row, text="Browse", command=self.select_batch_output)
        browse_btn.pack(side="right")
        
        # Video folder
        video_row = ctk.CTkFrame(self.main_frame)
        video_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(video_row, text="Video Folder:").pack(side="left")
        self.batch_video = ctk.CTkEntry(video_row)
        self.batch_video.pack(side="left", fill="x", expand=True, padx=5)
        self.batch_video.insert(0, self.batch_settings.settings["video_folder"])
        
        browse_btn = ctk.CTkButton(video_row, text="Browse", command=self.select_batch_video)
        browse_btn.pack(side="right")
        
        # Preset selection
        preset_row = ctk.CTkFrame(self.main_frame)
        preset_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(preset_row, text="Subtitle Preset:").pack(side="left")
        from subtitle_settings import SubtitlePresetManager
        preset_manager = SubtitlePresetManager()
        self.batch_preset = ctk.CTkComboBox(preset_row, values=list(preset_manager.presets.keys()))
        self.batch_preset.pack(side="left", fill="x", expand=True, padx=5)
        if self.batch_settings.settings["preset_name"]:
            self.batch_preset.set(self.batch_settings.settings["preset_name"])
            
        # File suffixes
        suffix_frame = ctk.CTkFrame(self.main_frame)
        suffix_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(suffix_frame, text="File Suffixes:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=5)
        
        suffixes = self.batch_settings.settings["suffixes"]
        self.suffix_entries = {}
        
        for key, value in suffixes.items():
            row = ctk.CTkFrame(suffix_frame)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{key.replace('_', ' ').title()}:").pack(side="left")
            entry = ctk.CTkEntry(row)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            entry.insert(0, value)
            self.suffix_entries[key] = entry
            
        # Save settings button
        save_btn = ctk.CTkButton(
            self.main_frame, 
            text="Save Settings",
            command=self.save_batch_settings,
            height=40
        )
        save_btn.pack(pady=10)
        
        # Process button
        process_btn = ctk.CTkButton(
            self.main_frame,
            text="Process All Files",
            command=self.process_batch,
            height=40,
            font=("Helvetica", 14, "bold")
        )
        process_btn.pack(pady=10)
        
        # Progress
        self.batch_progress = ctk.CTkProgressBar(self.main_frame)
        self.batch_progress.pack(fill="x", pady=10)
        self.batch_progress.set(0)
        
        self.batch_status = ctk.CTkLabel(self.main_frame, text="")
        self.batch_status.pack()
        
    def select_batch_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_input.delete(0, "end")
            self.batch_input.insert(0, folder)
            
    def select_batch_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_output.delete(0, "end")
            self.batch_output.insert(0, folder)
            
    def select_batch_video(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_video.delete(0, "end")
            self.batch_video.insert(0, folder)
            
    def save_batch_settings(self):
        """Save batch settings"""
        self.batch_settings.settings.update({
            "input_folder": self.batch_input.get(),
            "output_folder": self.batch_output.get(),
            "video_folder": self.batch_video.get(),
            "preset_name": self.batch_preset.get(),
            "suffixes": {k: v.get() for k, v in self.suffix_entries.items()}
        })
        self.batch_settings.save_settings()
        messagebox.showinfo("Success", "Settings saved!")
        
    def process_batch(self):
        """Process all matching files in batch, one at a time"""
        try:
            # Validate folders
            input_folder = self.batch_input.get()
            output_folder = self.batch_output.get()
            video_folder = self.batch_video.get()
            
            if not all([input_folder, output_folder, video_folder]):
                raise Exception("All folders must be specified!")
                
            if not all(os.path.exists(f) for f in [input_folder, output_folder, video_folder]):
                raise Exception("All folders must exist!")
                
            # Get subtitle settings
            preset_name = self.batch_preset.get()
            if not preset_name:
                raise Exception("Please select a subtitle preset!")
                
            from subtitle_settings import SubtitlePresetManager
            preset_manager = SubtitlePresetManager()
            settings = preset_manager.presets[preset_name]
                
            # Get all base names
            base_names = self.batch_settings.get_base_names()
            if not base_names:
                raise Exception("No valid files found in input folder!")
                
            # Process each file set sequentially
            total = len(base_names)
            self.batch_progress.set(0)
            
            for i, base_name in enumerate(base_names):
                try:
                    # Update progress and status
                    progress = (i / total) * 100
                    self.batch_progress.set(progress / 100)
                    self.batch_status.configure(text=f"Processing {base_name} ({i+1}/{total})")
                    self.update()
                    
                    # Find matching files
                    files = self.batch_settings.find_matching_files(base_name)
                    
                    # Skip if required files not found
                    if not files["audio"]:
                        print(f"Skipping {base_name}: No audio file found")
                        continue
                    
                    # Create new processor for each file to ensure clean state
                    processor = VideoProcessor(self.work_dir, output_folder)
                    
                    try:
                        # Process video
                        print(f"\nProcessing {base_name}...")
                        print(f"Files found: {files}")
                        
                        output = processor.process_video(
                            hook_mp3=files["hook"],
                            audio_mp3=files["audio"],
                            hook_srt=files["hook_subtitle"],
                            audio_srt=files["subtitle"],
                            thumbnail=files["thumbnail"],
                            video_folder=video_folder,
                            subtitle_settings=settings
                        )
                        
                        if output and os.path.exists(output):
                            print(f"Successfully processed {base_name}")
                            
                            # Copy .ass files to output folder
                            work_dir = processor.work_dir
                            code_dir = os.getcwd()  # Thư mục chứa code
                            for file in os.listdir(work_dir):
                                if file.endswith('.ass'):
                                    ass_path = os.path.join(work_dir, file)
                                    # Copy to output folder
                                    ass_output = os.path.join(output_folder, file)
                                    print(f"Copying ASS file to output: {ass_output}")
                                    shutil.copy2(ass_path, ass_output)
                                    # Copy to code directory
                                    ass_code = os.path.join(code_dir, file)
                                    print(f"Copying ASS file to code: {ass_code}")
                                    shutil.copy2(ass_path, ass_code)
                            
                    except Exception as e:
                        print(f"Error processing {base_name}: {e}")
                        raise e
                        
                except Exception as e:
                    error_msg = f"Failed to process {base_name}: {str(e)}"
                    print(error_msg)
                    if not messagebox.askyesno("Error", f"{error_msg}\n\nContinue with next file?"):
                        raise Exception("Batch processing cancelled by user")
            
            # Done
            self.batch_progress.set(1)
            self.batch_status.configure(text="Processing complete!")
            messagebox.showinfo("Success", f"Successfully processed {total} files!")
            
        except Exception as e:
            self.batch_status.configure(text="Error: " + str(e))
            messagebox.showerror("Error", str(e))
            
        finally:
            self.batch_progress.set(0)
            self.update()

def main():
    app = BatchProcessorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
