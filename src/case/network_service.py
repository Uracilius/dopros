import requests
import time
import os
from src.case.config import NETWORK_CHECK_URL, MP3_SAVE_DIR

os.makedirs(MP3_SAVE_DIR, exist_ok=True)


class NetworkService:
    """Continuously checks for network availability."""

    def __init__(self):
        self.online = self.is_online()
        self.monitor_networks = True

    def is_online(self) -> bool:
        """Checks internet connectivity by sending a request to a known URL."""
        try:
            requests.get(NETWORK_CHECK_URL, timeout=5)
            return True
        except requests.RequestException:
            return False

    def monitor_network(self, transcription_service):
        """Continuously monitors network and triggers TranscriptionService when online."""
        while self.monitor_networks:
            new_status = self.is_online()
            if new_status and not self.online:
                print("Network restored. Starting transcription fetcher.")
                transcription_service.fetch_transcriptions()
            self.online = new_status
            time.sleep(10)


if __name__ == "__main__":
    network_service = NetworkService()

    print("Hello!!!")
