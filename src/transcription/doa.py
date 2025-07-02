    # voice_direction.py

import usb.core
import usb.util
from src.transcription.tuning import Tuning

class VoiceDirectionFinder:
    def __init__(self, bucket_size=45, vendor_id=0x2886, product_id=0x0018):
        self.bucket_size = bucket_size
        dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if dev is None:
            raise ValueError("Microphone device not found.")
        print(f"[VDF] Microphone found (vendor=0x{vendor_id:04x}, product=0x{product_id:04x})")
        self.microphone = Tuning(dev)
        self.bucket_to_speaker = {}
        self.speaker_counter = 1

    def get_direction(self):
        doa = self.microphone.direction
        print(f"[VDF] Raw DOA: {doa:.1f}°")
        return doa

    def get_bucket(self, doa):
        bucket = int((doa % 360) / self.bucket_size)
        print(f"[VDF] DOA {doa:.1f}° → bucket {bucket}")
        return bucket

    def classify_speaker(self, bucket):
        if bucket not in self.bucket_to_speaker:
            name = f"Speaker {self.speaker_counter}"
            self.bucket_to_speaker[bucket] = name
            print(f"[VDF] New bucket {bucket} → {name}")
            self.speaker_counter += 1
        else:
            print(f"[VDF] Bucket {bucket} → existing {self.bucket_to_speaker[bucket]}")
        return self.bucket_to_speaker[bucket]
