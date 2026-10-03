"""Kameralardan gelen en güncel kareyi thread-safe biçimde tutan tampon.

Tanıma servisi her kamera için yalnızca "en son" kareyi işler; CPU yoğun
tespit/OCR adımları kare üretim hızına yetişemese bile birikme (backlog)
oluşmaz, en eski kareler sessizce atlanır (gerçek zamanlılık önceliklidir).
"""

from __future__ import annotations

import threading


class LatestFrameStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._frames: dict[int, tuple[int, object]] = {}
        self._last_consumed_seq: dict[int, int] = {}
        self._seq_counter = 0

    def put(self, camera_id: int, frame) -> None:
        with self._lock:
            self._seq_counter += 1
            self._frames[camera_id] = (self._seq_counter, frame)

    def get_if_new(self, camera_id: int):
        with self._lock:
            entry = self._frames.get(camera_id)
            if entry is None:
                return None
            seq, frame = entry
            if self._last_consumed_seq.get(camera_id) == seq:
                return None
            self._last_consumed_seq[camera_id] = seq
            return frame

    def active_camera_ids(self) -> list[int]:
        with self._lock:
            return list(self._frames.keys())

    def remove(self, camera_id: int) -> None:
        with self._lock:
            self._frames.pop(camera_id, None)
            self._last_consumed_seq.pop(camera_id, None)
