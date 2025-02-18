import json
import os
from typing import Dict, Optional

class BatchSettings:
    def __init__(self, settings_file: str = "batch_settings.json"):
        self.settings_file = settings_file
        self.settings = self.load_settings()
        
    def load_settings(self) -> Dict:
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return {
            "input_folder": "",
            "output_folder": "",
            "video_folder": "",
            "preset_name": "",
            "suffixes": {
                "audio": "_audio",  # Required
                "hook": "_hook",    # Optional
                "subtitle": "_audio",  # Required (same as audio by default)
                "hook_subtitle": "_hook",  # Optional (same as hook by default)
                "thumbnail": "_Hook"  # Optional
            }
        }
        
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def find_matching_files(self, base_name: str) -> Dict[str, Optional[str]]:
        """Find all matching files for a given base name, case insensitive
        
        Args:
            base_name: Base name of the file set (e.g. 'KB2' for 'KB2_audio.wav')
            
        Returns:
            Dictionary of file types and their paths
        """
        input_folder = self.settings["input_folder"]
        suffixes = self.settings["suffixes"]
        
        result = {
            "audio": None,
            "hook": None,
            "subtitle": None,
            "hook_subtitle": None,
            "thumbnail": None
        }
        
        # Convert base name and suffixes to lower case for comparison
        base_name_lower = base_name.lower()
        suffix_map = {k: v.lower() for k, v in suffixes.items()}
        
        # Find all matching files
        for file in os.listdir(input_folder):
            file_path = os.path.join(input_folder, file)
            file_lower = file.lower()
            
            # Required: Audio file
            if file_lower.startswith(base_name_lower + suffix_map["audio"]):
                if file_lower.endswith(('.wav', '.mp3')):
                    result["audio"] = file_path
                elif file_lower.endswith('.srt'):
                    result["subtitle"] = file_path
                    
            # Optional: Hook files
            if suffix_map["hook"] and file_lower.startswith(base_name_lower + suffix_map["hook"]):
                if file_lower.endswith(('.wav', '.mp3')):
                    result["hook"] = file_path
                elif file_lower.endswith('.srt'):
                    result["hook_subtitle"] = file_path
                    
            # Optional: Thumbnail
            if suffix_map["thumbnail"] and file_lower.startswith(base_name_lower + suffix_map["thumbnail"]):
                if file_lower.endswith(('.png', '.jpg', '.jpeg')):
                    result["thumbnail"] = file_path
        
        return result
        
    def get_base_names(self) -> list:
        """Get all unique base names from the input folder, case insensitive"""
        input_folder = self.settings["input_folder"]
        if not input_folder or not os.path.exists(input_folder):
            return []
            
        # Get all audio files (required)
        audio_suffix = self.settings["suffixes"]["audio"].lower()
        base_names = set()
        
        for file in os.listdir(input_folder):
            file_lower = file.lower()
            if file_lower.endswith(('.wav', '.mp3')) and audio_suffix in file_lower:
                # Remove suffix and extension to get base name
                base_name = file_lower.split(audio_suffix)[0]
                base_names.add(base_name)
                
        return sorted(list(base_names))
