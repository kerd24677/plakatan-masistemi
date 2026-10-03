@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  Plaka Tanima Sistemi - Windows Build
echo ============================================

if not exist .venv (
    echo [1/6] Sanal ortam olusturuluyor...
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo HATA: Sanal ortam olusturulamadi. Python 3.11 kurulu mu? ^(py -3.11 -V^)
        exit /b 1
    )
)
call .venv\Scripts\activate.bat

echo [2/6] Bagimliliklar kuruluyor...
pip install --upgrade pip
pip install -r requirements-build.txt
if errorlevel 1 (
    echo HATA: Bagimliliklar kurulamadi.
    exit /b 1
)

echo.
echo [UYARI] Tesseract OCR motoru bu scriptle KURULMAZ. Devam etmeden once
echo         https://github.com/UB-Mannheim/tesseract/wiki adresinden
echo         Tesseract-OCR'i kurup PATH'e eklediginizden emin olun, ya da
echo         vendor\tesseract\ klasorune tesseract.exe + tessdata'yi
echo         kopyalayarak tam bagimsiz (self-contained) bir dagitim hazirlayin.
echo.

echo [3/6] Testler calistiriliyor...
pytest -q
if errorlevel 1 (
    echo HATA: Testler basarisiz oldu, derleme durduruldu.
    exit /b 1
)

echo [4/6] Klasor tabanli EXE derleniyor ^(onedir, birincil dagitim^)...
pyinstaller --noconfirm plakatanima.spec
if errorlevel 1 (
    echo HATA: Klasor tabanli derleme basarisiz oldu.
    exit /b 1
)

echo [5/6] Tek dosyali EXE derleniyor ^(onefile, opsiyonel^)...
pyinstaller --noconfirm plakatanima_onefile.spec
if errorlevel 1 (
    echo UYARI: Tek dosyali derleme basarisiz oldu. Klasor tabanli dagitimi kullanin.
)

echo [6/6] Kurulum paketi olusturuluyor ^(Inno Setup^)...
where iscc >nul 2>nul
if errorlevel 1 (
    echo UYARI: Inno Setup ^(ISCC.exe^) PATH'te bulunamadi, kurulum paketi atlandi.
    echo        https://jrsoftware.org/isdl.php adresinden kurup build.bat'i tekrar calistirin.
) else (
    if not exist installer_output mkdir installer_output
    iscc installer\plakatanima_installer.iss
)

echo.
echo ============================================
echo  Derleme tamamlandi
echo ============================================
echo Klasor tabanli EXE : dist\PlakaTanimaSistemi\PlakaTanimaSistemi.exe
echo Tek dosyali EXE     : dist\PlakaTanimaSistemiOneFile.exe  ^(uretildiyse^)
echo Kurulum paketi      : installer_output\PlakaTanimaSistemi_Setup.exe ^(uretildiyse^)

endlocal
