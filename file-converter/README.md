# Universal File Converter

A simple drag-and-drop Windows app for converting images, documents, and
audio/video files. No install, no command line — just download the `.exe`
and run it.

## Download

Grab the latest `FileConverter.exe` from the [Releases page](../../releases).
No Python or extra software needed — just double-click it.

> First run may trigger a Windows SmartScreen warning because the app isn't
> code-signed. Click **More info -> Run anyway**. This is expected for any
> unsigned indie app.

## What it converts

| Category | Formats |
|---|---|
| Images | PNG, JPEG, WEBP, BMP, GIF, TIFF, ICO, HEIC (read) |
| Documents | DOCX -> PDF*, PDF -> DOCX, PDF -> TXT, DOCX -> TXT, TXT <-> MD |
| Video/Audio | MP4, MOV, AVI, MKV, WEBM, MP3, WAV, FLAC, M4A, OGG |

\* DOCX -> PDF requires Microsoft Word to be installed (it drives Word directly).
All other conversions work standalone.

## How to use it

1. Open the app.
2. Drag files into the window (or click **Add Files...**).
3. Pick the output format from the dropdown.
4. Choose where to save the converted files (defaults to a `converted`
   subfolder next to your originals).
5. Click **Convert**.

## Running from source

```bash
git clone https://github.com/<your-username>/file-converter.git
cd file-converter
pip install -r requirements.txt
python app.py
```

## Building the .exe yourself

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name FileConverter \
    --collect-all tkinterdnd2 --collect-all imageio_ffmpeg app.py
```

The finished `.exe` lands in `dist/`.

This repo's GitHub Actions workflow (`.github/workflows/build.yml`) does this
automatically on Windows runners and attaches the `.exe` to a GitHub Release
whenever you push a tag like `v1.0.0`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Project structure

```
app.py                  # Tkinter GUI
converters/
  images.py              # Pillow-based image conversion
  documents.py            # docx/pdf/txt conversion
  video.py                 # ffmpeg-based audio/video conversion
requirements.txt
.github/workflows/build.yml  # CI: builds & releases the .exe
```

## License

MIT — see [LICENSE](LICENSE).
