import json
import logging
import tempfile
from os import getenv

from moviepy.editor import VideoFileClip

import azure.functions as func
from azure.storage.blob import BlobClient
import azure.cognitiveservices.speech as speechsdk

def main(event: func.EventGridEvent):
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    })
    logging.info('Python EventGrid trigger processed an event: %s', result)
    
    # Get blob from event data
    container_name, blob_name = event.subject.split("/")[-3], event.subject.split("/")[-1]
    blob = BlobClient.from_connection_string(
        conn_str=getenv("CONNECTION_STRING"),
        container_name=container_name,
        blob_name=blob_name
    )
    
    # Write blob to temporary storage
    temp_dir_path = tempfile.gettempdir()
    video_path = f"{temp_dir_path}/{blob_name}"
    with open(video_path, "wb") as my_blob:
        blob_data = blob.download_blob()
        blob_data.readinto(my_blob)

    # extract audio from video
    audio_path = f"{video_path}_audio.wav"
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)

    # get speech credentials
    subscription_key = getenv("SUBSCRIPTION_KEY")
    speech_region = getenv("REGION")

    # Authenticate
    speech_config = speechsdk.SpeechConfig(subscription_key, speech_region)
    
    # Set up speech recogniser to spit out transcription
    audio_config = speechsdk.AudioConfig(filename=audio_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    logging.info(f"Transcription: {speech_recognition_result.text}")

    # Write transcription to blob storage
    transcript_filename = f"{blob_name}_transcript.txt"
    transcript_blob = BlobClient.from_connection_string(
        conn_str=getenv("CONNECTION_STRING"), 
        container_name="transcripts",
        blob_name=transcript_filename
    )
    logging.info("blob instantiated")
    transcript_blob.upload_blob(speech_recognition_result.text, overwrite=True)
    logging.info(f"Sucessfully uploaded transcript to {container_name} under blob name {transcript_filename}")
    