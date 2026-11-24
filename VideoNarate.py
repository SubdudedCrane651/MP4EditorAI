from moviepy import VideoFileClip, AudioFileClip

video = VideoFileClip("Meal Planner.mp4")
narration = AudioFileClip("tts_output.wav")

final = video.with_audio(narration)

final.write_videofile(
    "output.mp4",
    codec="libx264",
    audio_codec="aac"
)