import os
import tempfile
from pathlib import Path
from faster_whisper import WhisperModel
import traceback



def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def extract_subtitles_with_whisper(video_path, output_path=None, local_model_path="", device="cpu", log_callback=None, stop_callback=None):
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_path is None:
        video_file = Path(video_path)
        output_path = video_file.parent / f"{video_file.stem}.srt"

    try:
        if local_model_path and Path(local_model_path).exists():
            print(f"Using local model: {local_model_path} on device: {device}")
            if log_callback:
                log_callback(f"Using local model: {local_model_path} on device: {device}")
            model = WhisperModel(local_model_path, device=device)
        else:
            if local_model_path:
                print(f"Local model path not found")
            if log_callback:
                log_callback(f"Local model path not found")

    except Exception as e:
        print(f"Model loading error: {e}")
        if log_callback:
            log_callback(f"Model loading error: {e}")
        raise
    
    print("Model prepared, starting transcription...")
    if log_callback:
        log_callback("Model prepared, starting transcription...")
    
    try:
        segments, info = model.transcribe(video_path, language=None)
    except Exception as e:
        print(f"Transcription failed: {e}")
        traceback.print_exc()
        if log_callback:
            log_callback(f"Transcription failed: {e}")
    
    srt_content = ""
    segment_count = 0
    for i, segment in enumerate(segments, 1):
        # Check if stop was requested
        if stop_callback and stop_callback():
            print("Transcription stopped by user request")
            if log_callback:
                log_callback("Transcription stopped by user request")
            break
            
        start_time = format_timestamp(segment.start)
        end_time = format_timestamp(segment.end)
        text = segment.text.strip()
        
        log_message = f"{i}: {start_time} --> {end_time} | {text}"
        print(log_message)
        if log_callback:
            log_callback(log_message)
            
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
        segment_count = i

    # Only save if not stopped or if we have some content
    if srt_content and not stop_callback:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        print(f"Subtitles saved to: {output_path} ({segment_count} segments)")
        if log_callback:
            log_callback(f"Subtitles saved to: {output_path} ({segment_count} segments)")
    else:
        print("No subtitles were generated or process was stopped immediately")
        if log_callback:
            log_callback("No subtitles were generated or process was stopped immediately")
    
    return str(output_path)