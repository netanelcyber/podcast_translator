#!/usr/bin/env python3
"""
Podcast Translator – Auto Speaker Detection
- מזהה אוטומטית מספר דוברים
- שמות אוטומטיים לכל דובר
- סגנון דיבור מותאם אישית
- תרגום לעברית
- יצירת MP3 איכותי עם ffmpeg בלבד
"""

import os
import sys
import subprocess
import re

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import google.cloud.speech as speech
except ImportError:
    install("google-cloud-speech")
    import google.cloud.speech as speech

try:
    import google_genai as genai
except ImportError:
    install("google-genai")
    import google_genai as genai

try:
    import regex
except ImportError:
    install("regex")
    import regex

def check_ffmpeg():
    try:
        subprocess.check_output(["ffmpeg", "-version"])
    except Exception:
        print("❌ FFmpeg לא נמצא במערכת. התקן אותו והוסף ל-PATH.")
        sys.exit(1)
check_ffmpeg()

AUDIO_PATH = "podcast.mp3"
OUTPUT_AUDIO_PATH = "translated_podcast_final.mp3"

STYLE_VOICES = {
    "formal": {"voice": "he-IL-Wavenet-M", "rate": 1.0, "pitch": 0.0},
    "casual": {"voice": "he-IL-Wavenet-F", "rate": 1.1, "pitch": 2.0},
}

speech_client = speech.SpeechClient()
genai_client = genai.Client()

def diarize_audio(audio_path):
    print("🔍 מזהה דוברים אוטומטי...")
    with open(audio_path, "rb") as f:
        content = f.read()
    audio_obj = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=44100,
        language_code="en-US",
        enable_speaker_diarization=True,
        enable_automatic_punctuation=True,
        model="latest_long",
        use_enhanced=True
    )
    response = speech_client.recognize(config=config, audio=audio_obj)
    segments = []
    speaker_ids = set()
    for result in response.results:
        for alt in result.alternatives:
            for word_info in alt.words:
                speaker_ids.add(word_info.speaker_tag)
                segments.append({"speaker": word_info.speaker_tag, "word": word_info.word})
    print(f"✅ זוהו {len(speaker_ids)} דוברים.")
    return segments, list(speaker_ids)

def merge_words_to_sentences(segments):
    merged = {}
    for seg in segments:
        spk = seg["speaker"]
        if spk not in merged:
            merged[spk] = []
        merged[spk].append(seg["word"])
    return {spk: " ".join(words) for spk, words in merged.items()}

def assign_speaker_names(sentences):
    speaker_names = {}
    for spk, text in sentences.items():
        matches = re.findall(r'\b[A-Z][a-z]+\b', text)
        name = matches[0] if matches else f"Speaker{spk}"
        speaker_names[spk] = name
    return speaker_names

def detect_speech_style(text):
    if len(text.split()) > 20 or any(word in text.lower() for word in ["sir", "madam", "official"]):
        return "formal"
    else:
        return "casual"

def translate_text_to_hebrew(text):
    prompt = f"Translate the following English text to fluent Hebrew:\n\n{text}"
    response = genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt]
    )
    return response.text.strip()

def text_to_speech(text, speaker_name, style, index):
    params = STYLE_VOICES.get(style, STYLE_VOICES["casual"])
    output_file = f"temp_{speaker_name}_{index}.mp3"
    audio = genai_client.models.generate_audio(
        model="gemini-2.5-flash-tts",
        contents=[text],
        voice=params["voice"],
        sample_rate_hz=24000,
        speaking_rate=params["rate"],
        pitch=params["pitch"]
    )
    with open(output_file, "wb") as f:
        f.write(audio)
    return output_file

def concat_mp3_files(mp3_files, output_file):
    list_file = "mp3_list.txt"
    with open(list_file, "w") as f:
        for mp3 in mp3_files:
            f.write(f"file '{os.path.abspath(mp3)}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_file
    ], check=True)
    os.remove(list_file)
    for mp3 in mp3_files:
        os.remove(mp3)

def process_audio(audio_path, output_path):
    segments, speaker_ids = diarize_audio(audio_path)
    sentences = merge_words_to_sentences(segments)
    speaker_names = assign_speaker_names(sentences)

    temp_mp3_files = []
    for idx, (spk, text) in enumerate(sentences.items(), start=1):
        name = speaker_names[spk]
        style = detect_speech_style(text)
        print(f"🗣️ {name} ({style}): {text[:60]}...")
        hebrew_text = translate_text_to_hebrew(text)
        temp_file = text_to_speech(hebrew_text, name, style, idx)
        temp_mp3_files.append(temp_file)

    concat_mp3_files(temp_mp3_files, output_path)
    print(f"\n✅ הסתיים! הקובץ הסופי: {output_path}")

def main():
    if not os.path.exists(AUDIO_PATH):
        print(f"❌ קובץ לא נמצא: {AUDIO_PATH}")
    else:
        process_audio(AUDIO_PATH, OUTPUT_AUDIO_PATH)

if __name__ == "__main__":
    main()
