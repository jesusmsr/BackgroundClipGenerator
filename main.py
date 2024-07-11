import gradio as gr
import webbrowser
from pytube import YouTube
import os

DOWNLOAD_PATH = 'output/temp'

def greet(name, intensity):
    return "Hello, " + name + "!" * int(intensity)

def download_videos(urls):
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
        
    urls = urls.split("\n")  # Split the input by new lines to get individual URLs
    download_paths = []
    for url in urls:
        url = url.strip()
        if url:
            try:
                yt = YouTube(url)
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                output_path = stream.download(output_path=DOWNLOAD_PATH)
                download_paths.append(f"Downloaded: {output_path}")
            except Exception as e:
                download_paths.append(f"Failed to download {url}: {str(e)}")
    return "\n".join(download_paths)

iface = gr.Interface(
    fn=download_videos,
    inputs=gr.TextArea(placeholder="Enter YouTube URLs separated by new lines..."),
    outputs="text",
    title="YouTube Video Downloader",
    description="Paste YouTube URLs separated by new lines and click 'Submit' to download."
)


webbrowser.open_new("http://127.0.0.1:7860")
iface.launch()

