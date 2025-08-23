# C790 & X1300 HDMI to CSI-2 Capture on Raspberry Pi 5

Dieses Repository demonstriert Live-Capture einer HDMI-Quelle – z.B. eines Desktop-PCs – über die Geekworm X1300 (TC358743) nach CSI-2 auf einen Raspberry Pi 5 mit Raspberry Pi OS (X11).

Die Capture-Pipeline wird über ein Shell-Skript vorbereitet und anschließend mit einem kurzen Python-Programm geöffnet.

## Voraussetzungen

- Raspberry Pi 5 mit Raspberry Pi OS (X11)
- Zugriff auf die Kommandozeile (sudo-Rechte)
- Python 3 inklusive OpenCV (`sudo apt install python3-opencv`)
- v4l2-ctl und media-ctl (`sudo apt install v4l-utils`)
- Optional: ffplay für die Vorschau (`sudo apt install ffmpeg`)

## Verwendung

1. **Setup des Capture-Geräts**

   ```bash
   ./opencv_setup.sh
   ```

   Das Skript konfiguriert den rp1-cfe Treiber, setzt die Media-Links und richtet das Video-Device auf RGB3 ein.
   Mit der Option `--preview` wird eine einfache Vorschau mit ffplay gestartet:

   ```bash
   ./opencv_setup.sh --preview
   ```

2. **Live-Capture starten**

   Nach erfolgreichem Setup kann der Stream mit OpenCV angezeigt werden:

   ```bash
   python3 opencv_capture.py
   ```

   Es erscheint ein Fenster mit dem Live-Bild. Mit `q` wird die Anzeige beendet.

## Troubleshooting

Falls das Video-Device belegt oder fehlerhaft konfiguriert ist, können alle
potenziellen Leser geschlossen und das Setup erneut ausgeführt werden:

```bash
sudo fuser -kv /dev/video0 /dev/v4l-subdev* /dev/media* || true
./opencv_setup.sh
```

## Lizenz

Siehe jeweilige Lizenzbedingungen der genutzten Komponenten. Dieses Repository stellt lediglich ein Beispiel für die Inbetriebnahme dar.

