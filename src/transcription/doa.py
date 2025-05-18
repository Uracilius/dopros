# src/transcription/voice_direction.py
import usb.core, usb.util, threading, time
from collections import deque
from dateutil.tz import tzlocal
from src.transcription.tuning import Tuning


class VoiceDirectionFinder:
    def __init__(self, bucket_size=45, vendor_id=0x2886, product_id=0x0018):
        self.bucket_size = bucket_size
        dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if dev is None:
            raise ValueError("Microphone device not found.")
        self.microphone = Tuning(dev)
        self.bucket_to_speaker = {}
        self.speaker_counter = 1
        self.last_bucket = None

    def get_bucket(self, doa):
        return int((doa % 360) / self.bucket_size)

    def get_direction(self):
        return self.microphone.direction

    def classify_speaker(self, doa):
        bucket = self.get_bucket(doa)
        if bucket not in self.bucket_to_speaker:
            self.bucket_to_speaker[bucket] = f"Speaker {self.speaker_counter}"
            self.speaker_counter += 1
        return self.bucket_to_speaker[bucket]
