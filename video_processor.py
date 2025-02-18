import os
import subprocess
from pydub import AudioSegment
import glob
from typing import Optional, List, Tuple
import re
import math
import random
import pysubs2
import time
import json
import shutil

class VideoProcessor:
    def __init__(self, work_dir: str, output_folder: str):
        self.work_dir = work_dir
        self.output_folder = output_folder
        self.temp_dir = work_dir  # Use work_dir directly for temp files
        os.makedirs(self.temp_dir, exist_ok=True)
        self.timestamp = int(time.time())  # Thêm timestamp cho temp files

    def cleanup(self):
        """Clean up all temporary files in work directory"""
        try:
            # Remove all files in temp directory
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    try:
                        os.remove(file_path)
                        print(f"Removed temp file: {file}")
                    except Exception as e:
                        print(f"Error removing {file}: {e}")
                print("Cleaned up temp directory")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def get_temp_path(self, prefix: str, suffix: str) -> str:
        """Tạo đường dẫn file tạm thởi với timestamp để tránh trùng
        
        Args:
            prefix: Tiền tố của file (ví dụ: 'hook', 'main')
            suffix: Hậu tố của file (ví dụ: '.mp3', '.ass')
        """
        return os.path.join(self.temp_dir, f"{prefix}_{self.timestamp}{suffix}")

    def get_audio_duration(self, audio_path: str) -> float:
        """Lấy thời lượng của file audio"""
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ]
        duration = float(subprocess.check_output(cmd).decode().strip())
        return duration

    def prepare_and_get_duration(self, hook_mp3: Optional[str], audio_mp3: str) -> Tuple[str, float]:
        """Ghép audio và trả về đường dẫn file final + thời lượng chính xác"""
        final_audio = audio_mp3
        if hook_mp3:
            final_audio = self.get_temp_path("merged", ".mp3")  # Lưu ở thư mục tạm
            print(f"Merging hook ({hook_mp3}) with audio ({audio_mp3})")
            
            # Ghép audio
            def load_audio(path):
                ext = os.path.splitext(path)[1].lower()
                if ext == '.mp3':
                    return AudioSegment.from_mp3(path)
                elif ext == '.wav':
                    return AudioSegment.from_wav(path)
                else:
                    raise ValueError(f"Unsupported audio format: {ext}")
            
            try:
                hook = load_audio(hook_mp3)
                audio = load_audio(audio_mp3)
                print(f"Hook duration: {len(hook)/1000:.2f}s")
                print(f"Audio duration: {len(audio)/1000:.2f}s")
                
                merged = hook + audio
                print(f"Merged duration: {len(merged)/1000:.2f}s")
                merged.export(final_audio, format="mp3")
                print(f"Exported merged audio to: {final_audio}")
            except Exception as e:
                print(f"Error merging audio: {e}")
                raise

        # Lấy thời lượng chính xác
        duration = self.get_audio_duration(final_audio)
        print(f"Final audio duration: {duration:.2f}s")
        return final_audio, duration

    def merge_srt_files(self, srt_files: List[Tuple[str, float]]) -> Optional[str]:
        """Merge nhiều file SRT thành một, với offset cho từng file
        
        Args:
            srt_files: List of (srt_path, offset) tuples - offset in seconds
        """
        try:
            if not srt_files:
                return None
                
            if len(srt_files) == 1:
                # Nếu chỉ có 1 file và không cần offset thì dùng luôn
                if srt_files[0][1] == 0:
                    return srt_files[0][0]
            
            # Đọc và merge tất cả subtitle
            merged_subs = None
            for srt_path, offset in srt_files:
                try:
                    subs = pysubs2.load(srt_path, encoding='utf-8')
                    print(f"Successfully loaded SRT file: {srt_path}")
                    
                    # Apply offset nếu cần
                    if offset > 0:
                        offset_ms = int(offset * 1000)  # Convert to milliseconds
                        for line in subs:
                            old_start = line.start
                            line.start += offset_ms
                            line.end += offset_ms
                            print(f"Line timing: {old_start}ms -> {line.start}ms (offset: +{offset_ms}ms)")
                    
                    if merged_subs is None:
                        merged_subs = subs
                    else:
                        merged_subs.events.extend(subs.events)
                except Exception as e:
                    print(f"Error loading subtitle file {srt_path}: {e}")
                    return None
            
            # Sắp xếp lại theo thời gian
            if merged_subs:
                merged_subs.events.sort(key=lambda x: x.start)
                
                # Lưu file merged SRT
                output_path = self.get_temp_path('merged', '.srt')
                merged_subs.save(output_path)
                print(f"Successfully merged {len(srt_files)} SRT files to: {os.path.basename(output_path)}")
                return output_path
                
            return None
            
        except Exception as e:
            print(f"Error merging SRT files: {e}")
            return None

    def convert_srt_to_ass(self, srt_path: str, offset: float = 0, subtitle_settings=None) -> str:
        """Chuyển đổi SRT sang ASS với offset thời gian và subtitle settings
        
        Args:
            srt_path (str): Đường dẫn file SRT
            offset (float): Thời gian offset (giây), có thể là số thập phân (ví dụ: 10.534)
            subtitle_settings: Cài đặt subtitle (font, size, etc.)
        """
        try:
            if not srt_path:
                return None
                
            # Đọc subtitle
            try:
                subs = pysubs2.load(srt_path, encoding='utf-8')
                print(f"Successfully loaded SRT file: {srt_path}")
            except Exception as e:
                print(f"Error loading subtitle file: {e}")
                return None
            
            # Tạo style mặc định cho video dọc
            style = pysubs2.SSAStyle(
                fontname="Ubuntu Bold",
                fontsize=20,
                primarycolor="&HFFFFFF&",  # Trắng
                outlinecolor="&H000000&",  # Đen
                backcolor="&H000000&",     # Đen
                bold=0,
                italic=0,
                outline=2,    # Độ dày outline
                shadow=1,     # Độ dày shadow
                alignment=5,  # Middle-center cho video dọc
                marginv=20,   # Margin dọc
                marginl=20,   # Margin trái
                marginr=20    # Margin phải
            )
            
            # Cập nhật style từ subtitle_settings nếu có
            if subtitle_settings:
                # Map field names
                field_mapping = {
                    'font': 'fontname',
                    'font_size': 'fontsize',
                    'primary_color': 'primarycolor',
                    'outline_color': 'outlinecolor',
                    'back_color': 'backcolor',
                    'outline': 'outline',
                    'shadow': 'shadow',
                    'margin_v': 'marginv',
                    'margin_h': 'marginl',  # Use marginl for horizontal margin
                    'alignment': 'alignment'
                }
                
                # Áp dụng settings
                for preset_field, style_field in field_mapping.items():
                    if hasattr(subtitle_settings, preset_field):
                        value = getattr(subtitle_settings, preset_field)
                        if preset_field in ['font_size', 'outline', 'shadow', 'margin_v', 'margin_h', 'alignment']:
                            value = int(str(value))
                        # Set right margin equal to left margin
                        setattr(style, style_field, value)
                        if preset_field == 'margin_h':
                            setattr(style, 'marginr', value)
            
            # Thêm style vào subtitle
            subs.styles["Default"] = style
            
            # Áp dụng style và offset cho tất cả dòng
            print(f"Applying offset of {offset:.3f}s to all subtitles")
            for line in subs:
                line.style = "Default"
                
                # Xóa các tag ASS cũ nếu có
                text = line.text
                while '}{' in text:
                    text = text.replace('}{', '')
                text = text.strip('{}')
                
                # Thêm alignment vào text
                line.text = "{\\an%d}%s" % (style.alignment, text)
                
                # Thêm offset nếu có (giữ độ chính xác đến millisecond)
                if offset > 0:
                    old_start = line.start
                    old_end = line.end
                    # Convert offset từ giây sang millisecond, giữ độ chính xác
                    offset_ms = int(offset * 1000)  # 10.534s -> 10534ms
                    line.start += offset_ms
                    line.end += offset_ms
                    print(f"Line timing: {old_start}ms -> {line.start}ms (offset: +{offset_ms}ms)")
            
            # Lưu file ASS với timestamp
            base_name = os.path.splitext(os.path.basename(srt_path))[0]
            ass_path = os.path.join(self.work_dir, f"{base_name}_{self.timestamp}.ass")
            subs.save(ass_path)
            print(f"Created ASS file in work directory: {ass_path}")
            
            return ass_path
            
        except Exception as e:
            print(f"Error converting SRT to ASS: {str(e)}")
            return None

    def merge_ass_files(self, ass_files: List[str]) -> Optional[str]:
        """Ghép nhiều file ASS thành một file duy nhất, giữ nguyên timing và style của từng file

        Args:
            ass_files: Danh sách các file ASS cần ghép

        Returns:
            str: Đường dẫn tới file ASS đã ghép
        """
        try:
            if not ass_files:
                return None
                
            if len(ass_files) == 1:
                return ass_files[0]
                
            # Load tất cả file ASS
            all_subs = []
            for ass_file in ass_files:
                try:
                    subs = pysubs2.load(ass_file, encoding='utf-8')
                    all_subs.append(subs)
                    print(f"Loaded ASS file: {ass_file}")
                except Exception as e:
                    print(f"Error loading ASS file {ass_file}: {e}")
                    return None
            
            # Lấy file đầu tiên làm base
            merged_subs = all_subs[0]
            
            # Thêm style và events từ các file còn lại
            for i, subs in enumerate(all_subs[1:], 1):
                # Thêm styles mới (nếu có)
                for style_name, style in subs.styles.items():
                    if style_name not in merged_subs.styles:
                        new_style_name = f"{style_name}_{i}"
                        merged_subs.styles[new_style_name] = style
                        # Update style name trong events
                        for line in subs.events:
                            if line.style == style_name:
                                line.style = new_style_name
                
                # Thêm events
                merged_subs.events.extend(subs.events)
            
            # Sắp xếp lại events theo thời gian
            merged_subs.events.sort(key=lambda x: x.start)
            
            # Lưu file merged với timestamp
            output_path = self.get_temp_path('merged', '.ass')
            merged_subs.save(output_path)
            print(f"Successfully merged {len(ass_files)} ASS files to: {os.path.basename(output_path)}")
            
            return output_path
            
        except Exception as e:
            print(f"Error merging ASS files: {e}")
            return None

    def get_video_duration(self, video_path: str) -> float:
        """Lấy thời lượng của video
        
        Args:
            video_path: Đường dẫn đến file video
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0

    def prepare_background_videos(self, video_folder: str, total_duration: float) -> List[str]:
        """Chuẩn bị danh sách video background
        
        Args:
            video_folder: Thư mục chứa video background
            total_duration: Tổng thời lượng cần
        """
        try:
            # Lấy tất cả file mp4 trong thư mục
            video_files = []
            for file in os.listdir(video_folder):
                if file.endswith('.mp4'):
                    video_files.append(os.path.join(video_folder, file))
            
            if not video_files:
                raise Exception(f"No mp4 files found in {video_folder}")
            
            # Shuffle để random
            random.shuffle(video_files)
            
            # Nếu chỉ có 1 file thì dùng luôn
            if len(video_files) == 1:
                return video_files
            
            # Chọn đủ số file cần thiết
            selected_files = []
            current_duration = 0
            
            for video in video_files:
                duration = self.get_video_duration(video)
                if duration <= 0:
                    continue
                    
                selected_files.append(video)
                current_duration += duration
                
                # Nếu đã đủ thời lượng thì dừng
                if current_duration >= total_duration:
                    break
            
            if not selected_files:
                raise Exception("No valid background videos found")
                
            print(f"Selected {len(selected_files)} background videos, total duration: {current_duration:.2f}s")
            return selected_files
            
        except Exception as e:
            print(f"Error preparing background videos: {e}")
            return []

    def get_overlay_duration(self, hook_duration: float = 0) -> float:
        """Tính thời gian hiển thị overlay thumbnail
        - Nếu có hook: dùng hook_duration
        - Nếu không có hook: mặc định 5s
        """
        return hook_duration if hook_duration > 0 else 5.0

    def concat_background_videos(self, video_files: List[str], total_duration: float) -> Optional[str]:
        """Ghép tất cả video nền thành một file duy nhất
        
        Args:
            video_files: Danh sách các file video nền
            total_duration: Tổng thời lượng cần
        """
        try:
            if not video_files:
                return None
                
            # Tạo file concat.txt
            concat_file = self.get_temp_path('concat', '.txt')
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video in video_files:
                    f.write(f"file '{video}'\n")
            
            # Ghép các video lại
            output_path = self.get_temp_path('background', '.mp4')
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                '-t', str(total_duration),
                output_path
            ]
            
            print("Concatenating background videos...")
            subprocess.run(cmd, check=True)
            
            # Xóa file concat.txt
            os.remove(concat_file)
            
            return output_path
            
        except Exception as e:
            print(f"Error concatenating background videos: {e}")
            return None

    def process_video(self, 
                     hook_mp3: Optional[str],
                     audio_mp3: str,
                     hook_srt: Optional[str],
                     audio_srt: str,
                     thumbnail: Optional[str],
                     video_folder: str,
                     subtitle_settings=None,
                     callback=None) -> str:
        try:
            # 1. Chuẩn bị audio và lấy thời lượng
            if callback: callback("Preparing audio...", 10)
            
            # Lấy hook duration trước khi merge
            hook_duration = self.get_audio_duration(hook_mp3) if hook_mp3 else 0
            print(f"Hook duration: {hook_duration:.2f}s")
            
            # Merge audio và lấy tổng thời lượng
            final_audio, total_duration = self.prepare_and_get_duration(hook_mp3, audio_mp3)
            print(f"Total audio duration: {total_duration:.2f}s")

            # 2. Chuẩn bị subtitle
            if callback: callback("Converting subtitles...", 30)
            merged_ass = None
            if hook_srt or audio_srt:
                # Tạo list các file SRT và offset tương ứng
                srt_files = []
                if hook_srt:
                    srt_files.append((hook_srt, 0))  # Hook SRT đã có offset sẵn
                if audio_srt:
                    # Audio SRT luôn phải offset lên bằng hook_duration vì được ghép sau hook
                    srt_files.append((audio_srt, hook_duration))
                
                # Merge các file SRT
                merged_srt = self.merge_srt_files(srt_files)
                if not merged_srt:
                    raise Exception("Failed to merge SRT files")
                print(f"Using merged SRT file: {os.path.basename(merged_srt)}")
                
                # Convert merged SRT sang ASS, không cần offset vì đã offset trong merge_srt_files
                merged_ass = self.convert_srt_to_ass(merged_srt, 0, subtitle_settings)
                if not merged_ass:
                    raise Exception("Failed to convert merged SRT to ASS")
                print(f"Using merged ASS file: {os.path.basename(merged_ass)}")

            # 3. Chuẩn bị video background
            if callback: callback("Preparing background videos...", 20)
            background_videos = self.prepare_background_videos(video_folder, total_duration)
            if not background_videos:
                raise Exception("No background videos found")
                
            # 4. Ghép tất cả video nền thành một file
            if callback: callback("Concatenating background videos...", 40)
            background_video = self.concat_background_videos(background_videos, total_duration)
            if not background_video:
                raise Exception("Failed to concatenate background videos")
            print(f"Created background video: {os.path.basename(background_video)}")

            # 5. Tạo filter complex cho ffmpeg
            filter_complex = []
            
            # Add background video
            inputs = ['-i', background_video]
            filter_complex.append("[0:v]null[v0]")
            last_output = "v0"
            
            # Add subtitle nếu có
            if merged_ass:
                # Copy file ass về thư mục code trước khi xử lý video
                code_dir = os.getcwd()  # Thư mục chứa code
                final_ass = os.path.join(code_dir, os.path.basename(merged_ass))
                shutil.copy2(merged_ass, final_ass)
                print(f"Copied subtitle to code directory: {final_ass}")
                
                # Dùng file ass từ thư mục code
                filter_complex.append(f"[{last_output}]ass='{os.path.basename(final_ass)}'[subbed]")
                last_output = "subbed"
            
            # Add audio
            inputs.extend(['-i', final_audio])
            
            # Add thumbnail nếu có
            if thumbnail:
                inputs.extend(['-i', thumbnail])
                thumb_idx = 2  # background + audio + thumbnail
                overlay_duration = self.get_overlay_duration(hook_duration)
                print(f"Thumbnail overlay duration: {overlay_duration:.2f}s")
                
                # Thêm hiệu ứng fade cho thumbnail
                filter_complex.extend([
                    # Tạo overlay với fade out
                    f"[{thumb_idx}:v]fade=t=out:st={overlay_duration-0.5}:d=0.5[faded]",
                    
                    # Overlay thumbnail vào giữa video
                    f"[{last_output}][faded]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{overlay_duration})'[v]"
                ])
                last_output = "v"
            
            # Tạo command với fps và bitrate cố định
            cmd = [
                'ffmpeg', '-hwaccel', 'cuda', '-y'
            ] + inputs + [
                '-filter_complex', ';'.join(filter_complex),
                '-map', f'[{last_output}]',  # video output
                '-map', '1:a',  # audio output
                '-c:v', 'h264_nvenc',
                '-preset', 'p7',
                '-b:v', '5M',
                '-r', '30',  # 30fps
                '-c:a', 'aac'
            ]
            
            # Add duration if specified
            if total_duration:
                cmd.extend(['-t', str(total_duration)])
            
            # Tạo tên output từ tên audio và timestamp
            audio_name = os.path.splitext(os.path.basename(audio_mp3))[0]
            output_name = f"{audio_name}_{self.timestamp}.mp4"
            output_path = os.path.join(self.output_folder, output_name)  # Tạo trực tiếp trong output folder
            print(f"Output will be saved as: {output_path}")
            
            # Add output file
            cmd.append(output_path)
            
            # Thực thi command
            print("Executing command:", ' '.join(cmd))
            subprocess.run(cmd, check=True)
            
            # Đợi một chút để đảm bảo ffmpeg đã giải phóng hết file
            time.sleep(1)
            
            # Cleanup tất cả file tạm sau khi đã hoàn thành
            self.cleanup()
            
            if callback: callback("Done!", 100)
            return output_path
            
        except Exception as e:
            print(f"Error processing video: {str(e)}")
            return None