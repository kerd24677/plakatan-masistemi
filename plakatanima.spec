# -*- mode: python ; coding: utf-8 -*-
"""Klasör tabanlı (onedir) Windows dağıtımı için PyInstaller spec dosyası.
Windows üzerinde çalıştırın: pyinstaller --noconfirm plakatanima.spec
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
    [],
    exclude_binaries=True,
    name="PlakaTanimaSistemi",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="PlakaTanimaSistemi",
)
