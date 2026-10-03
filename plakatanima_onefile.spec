# -*- mode: python ; coding: utf-8 -*-
"""Tek dosyalı (onefile) Windows EXE için PyInstaller spec dosyası.

NOT: Büyük bağımlılıklar (PySide6, OpenCV) nedeniyle tek dosyalı EXE
başlangıçta kendini geçici bir klasöre açar; bu da ilk açılışı
yavaşlatabilir ve bazı ortamlarda (ör. kısıtlı yazma izni, antivirüs
engellemesi) sorun çıkarabilir. Birincil dağıtım yöntemi olarak
plakatanima.spec (klasör tabanlı/onedir) ÖNERİLİR; bu dosya ek bir
seçenek olarak sunulur.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH)
icon_path = project_root / "assets" / "icons" / "app.ico"

datas = [
    (str(project_root / "models"), "models"),
    (str(project_root / "assets"), "assets"),
]
# cv2'nin kendi paket verisi (haarcascade_*.xml dahil) PyInstaller'ın
# otomatik ikili/veri sınıflandırması tarafından ATLANABİLİR; açıkça
# toplanmazsa "Plaka tespit modeli bulunamadı" hatasıyla karşılaşılır.
datas += collect_data_files("cv2")
vendor_dir = project_root / "vendor"
if vendor_dir.exists():
    datas.append((str(vendor_dir), "vendor"))

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=["pytesseract", "cv2"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="PlakaTanimaSistemiOneFile",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
)
