from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.ui.screens.base import BaseScreen
from app.ui.widgets.camera_tile import CameraTile


class LiveViewScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Canlı Kamera İzleme")
        title.setObjectName("ScreenTitle")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(16)
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        self._tiles: dict[int, CameraTile] = {}
        self._rebuild()

    def on_activated(self) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tiles.clear()

        cameras = [c for c in self.ctx.camera_repo.list_all() if c.enabled]
        if not cameras:
            empty = QLabel(
                "Henüz etkin bir kamera yok. 'Kamera Yönetimi' ekranından "
                "kamera ekleyebilir veya test/demo modunu kullanabilirsiniz."
            )
            empty.setObjectName("ScreenSubtitle")
            self.grid.addWidget(empty, 0, 0)
            return

        columns = 2
        for i, camera in enumerate(cameras):
            tile = CameraTile(camera.id, camera.name)
            tile.set_status(camera.status)
            self._tiles[camera.id] = tile
            self.grid.addWidget(tile, i // columns, i % columns)

    def on_frame(self, camera_id: int, frame) -> None:
        tile = self._tiles.get(camera_id)
        if tile is not None:
            tile.update_frame(frame)

    def on_status(self, camera_id: int, status: str, error: str) -> None:
        tile = self._tiles.get(camera_id)
        if tile is not None:
            tile.set_status(status, error)
