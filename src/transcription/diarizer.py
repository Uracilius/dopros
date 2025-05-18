import math
from collections import deque, defaultdict


class SpeakerDiarizer:
    """
    Clusters DOA angles and assigns incremental speaker IDs.
    angle_tol = maximum angular distance (deg) to treat two speakers as the same.
    """

    def __init__(self, angle_tol: int = 25):
        self.angle_tol = angle_tol
        self.clusters: dict[int, float] = {}  # speaker_id -> centroid angle
        self.next_id = 1

    def _angle_dist(self, a, b):
        d = abs(a - b) % 360
        return min(d, 360 - d)

    def get_speaker_id(self, angle: float) -> int:
        # Match existing cluster
        for sid, centroid in self.clusters.items():
            if self._angle_dist(angle, centroid) <= self.angle_tol:
                # running-average centroid keeps clusters stable
                self.clusters[sid] = (centroid + angle) / 2
                return sid
        # New cluster → new speaker
        sid = self.next_id
        self.next_id += 1
        self.clusters[sid] = angle
        return sid
