import gradio as gr
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from moviepy.video.fx.all import resize, crop
from moviepy.video.io.ffmpeg_tools import ffmpeg_merge_video_audio

# Define the hardcoded download path
DOWNLOAD_PATH = "output"
CLIP_DURATION = 90  # Clip duration in seconds (1 minute and 30 seconds)
TARGET_RESOLUTION = (1080, 1920)  # Desired resolution (width, height)

def split_video(video_path, clip_duration, target_resolution):
    print("Starting video splitting...")
    video_clips = []
    video = VideoFileClip(video_path)
    video_duration = int(video.duration)
    
    target_width, target_height = target_resolution
    aspect_ratio = video.size[0] / video.size[1]
    
    # Calculate new width and height to maintain aspect ratio
    if video.size[0] / video.size[1] < target_width / target_height:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    
    # Resize video
    video = resize(video, newsize = (new_width, new_height))
    
    # Calculate crop positions to ensure the video is centered
    x_center = (new_width - target_width) / 2
    y_center = (new_height - target_height) / 2
    
    # Apply cropping
    video = crop(video, x1=x_center, y1=y_center, width=target_width, height=target_height)
    
    # Process and save clips
    for start_time in range(0, video_duration, clip_duration):
        end_time = start_time + clip_duration
        if end_time <= video_duration:
            clip = video.subclip(start_time, end_time)
            clip_path = f"{os.path.splitext(video_path)[0]}_clip_{start_time // clip_duration + 1}.mp4"
            clip.write_videofile(clip_path, codec='libx264', temp_audiofile='temp-audio.m4a', remove_temp=True, audio_codec='aac')
            video_clips.append(clip_path)
            print(f"Created clip: {clip_path}")
    
    video.close()
    return video_clips

def download_best_quality_video(yt, download_path):
    print("Downloading best quality video...")
    video_stream = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc().first()
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    video_path = video_stream.download(output_path=download_path, filename_prefix='video_')
    audio_path = audio_stream.download(output_path=download_path, filename_prefix='audio_')
    final_path = os.path.join(download_path, f"{yt.title.replace('/', '_')}.mp4")
    ffmpeg_merge_video_audio(video_path, audio_path, final_path, vcodec='copy', acodec='aac', ffmpeg_output=False, logger='bar')
    os.remove(video_path)
    os.remove(audio_path)
    print(f"Downloaded and merged to {final_path}")
    return final_path

def download_and_split_videos(urls, clip_length, width, height):
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)

    clip_duration = int(clip_length)
    target_resolution = (int(width), int(height))

    urls = urls.split("\n")
    download_paths = []
    for url in urls:
        url = url.strip()
        if url:
            try:
                yt = YouTube(url)
                print(f"Processing URL: {url}")
                output_path = download_best_quality_video(yt, DOWNLOAD_PATH)
                download_paths.append(f"Downloaded: {output_path}")
                clips = split_video(output_path, clip_duration, target_resolution)
                download_paths.extend([f"Created clip: {clip}" for clip in clips])
                os.remove(output_path)
            except Exception as e:
                print(f"Failed to process {url}: {e}")
                download_paths.append(f"Failed to download {url}: {str(e)}")
    return "\n".join(download_paths)

iface = gr.Interface(
    fn=download_and_split_videos,
    inputs=[
        gr.TextArea(placeholder="Enter YouTube URLs separated by new lines..."),
        gr.Textbox(placeholder="Enter clip length in seconds...", label="Clip Length (seconds)", value="90"),
        gr.Textbox(placeholder="Enter video width...", label="Width", value="1080"),
        gr.Textbox(placeholder="Enter video height...", label="Height", value="1920")],
    outputs="text",
    title="YouTube Video Downloader and Splitter",
    description="Paste YouTube URLs separated by new lines and click 'Submit' to download and split the videos."
)

iface.launch()
