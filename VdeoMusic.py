from moviepy import *
from moviepy.audio.AudioClip import CompositeAudioClip

video = VideoFileClip("video.mp4")
music = AudioFileClip("music.mp3").with_volume_scaled(0.2)

final_audio = CompositeAudioClip(
    [video.audio, music]
)

final_video = video.with_audio(final_audio)

final_video.write_videofile(
    "final.mp4",
    codec="libx264",
    audio_codec="aac"
)