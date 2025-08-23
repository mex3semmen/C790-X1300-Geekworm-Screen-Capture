#!/usr/bin/env bash
# X1300 (TC358743) → CSI-2 → RP1-CFE (Raspberry Pi 5, X11)
# Fest: CSI-Pads auf RGB888, Video-Node auf RGB3 (Bytes sind BGR → bgr24 anschauen)

set -Eeuo pipefail
log(){ echo "[X1300] $*"; }
die(){ echo "[X1300][FATAL] $*" >&2; exit 1; }
trap 'die "Abbruch in Zeile $LINENO."' ERR

[[ "${1:-}" == "--preview" ]] && PREVIEW=1 || PREVIEW=0

case "$(uname -r)" in 6.12*) log "WARN: Kernel 6.12.x macht mit TC358743 öfter Ärger; 6.6.x läuft stabiler."; ;; esac

# 0) Leser schließen (V4L2 meist Single-Reader)
for n in /dev/video* /dev/v4l-subdev* /dev/media*; do sudo fuser -kv "$n" >/dev/null 2>&1 || true; done

# 1) rp1-cfe Media-Device finden
MD=""
for m in /dev/media*; do sudo media-ctl -d "$m" -p 2>/dev/null | grep -q "rp1-cfe" && { MD="$m"; break; }; done
[[ -n "$MD" ]] || die "rp1-cfe Media-Device nicht gefunden."

# 2) Subdev (tc358743) + Video-Node (rp1-cfe-csi2_ch0) ermitteln
SUBDEV=""; for s in /dev/v4l-subdev*; do n="/sys/class/video4linux/$(basename "$s")/name"; [[ -f "$n" ]] && grep -q "^tc358743" "$n" && { SUBDEV="$s"; break; }; done
[[ -n "$SUBDEV" ]] || die "tc358743 Subdev fehlt."
VID=""; for v in /dev/video*; do n="/sys/class/video4linux/$(basename "$v")/name"; [[ -f "$n" ]] && grep -q "rp1-cfe-csi2_ch0" "$n" && { VID="$v"; break; }; done
[[ -n "$VID" ]] || die "rp1-cfe-csi2_ch0 Video-Node fehlt."

log "Media : $MD"
log "Subdev: $SUBDEV (tc358743)"
log "Video : $VID   (rp1-cfe-csi2_ch0)"

# 3) DV-Timings vom HDMI-Sender übernehmen (ggf. Fallback)
if ! sudo v4l2-ctl -d "$SUBDEV" --set-dv-bt-timings=query >/dev/null 2>&1; then
  log "Kein Handshake → setze 1080p60 & re-query."
  sudo v4l2-ctl -d "$SUBDEV" --set-dv-bt-timings=cea-1920x1080-60 >/dev/null 2>&1 || true
  sudo v4l2-ctl -d "$SUBDEV" --set-dv-bt-timings=query >/dev/null 2>&1 || die "Weiter kein HDMI-Signal."
fi
W=$(sudo v4l2-ctl -d "$SUBDEV" --query-dv-timings | awk '/Active width/{print $3}')
H=$(sudo v4l2-ctl -d "$SUBDEV" --query-dv-timings | awk '/Active height/{print $3}')
[[ "$W" != "0" && "$H" != "0" ]] || die "DV-Timings 0x0 → Quelle sendet nichts."
log "dv.current: ${W}x${H}"

# 4) Media-Graph reset + Link setzen
sudo media-ctl -d "$MD" -r
sudo media-ctl -d "$MD" -l "'csi2':4 -> 'rp1-cfe-csi2_ch0':0 [1]"

# Bridge-Entity-Namen (für tc358743:0) extrahieren
BR="$(sudo media-ctl -d "$MD" -p | sed -n "s/.*entity .*: \(tc358743 [^)]*\)).*/\1/p" | head -n1 | sed 's/)$//')"
[[ -n "$BR" ]] || BR="tc358743 11-000f"

# 5) CSI auf RGB888 drehen (wie Geekworm-Doku) – Pads: Bridge:0, csi2:0 (Sink), csi2:4 (Source)
#    Eventuelles 'Invalid argument (22)' an nicht betroffenen Pads ist kosmetisch → ignorieren.
sudo media-ctl -d "$MD" -V "'$BR':0  [fmt:RGB888_1X24/${W}x${H} field:none colorspace:srgb]" || true
sudo media-ctl -d "$MD" -V "'csi2':0  [fmt:RGB888_1X24/${W}x${H} field:none colorspace:srgb]"
sudo media-ctl -d "$MD" -V "'csi2':4  [fmt:RGB888_1X24/${W}x${H} field:none colorspace:srgb]"

# 6) Video-Node auf RGB3 (Achtung: Bytes sind BGR-Reihenfolge → bgr24)
sudo v4l2-ctl -d "$VID" --set-fmt-video=width=${W},height=${H},pixelformat=RGB3

# 7) Smoketest
sudo v4l2-ctl -d "$VID" --stream-mmap=4 --stream-count=60 --stream-to=/dev/null >/dev/null
log "Stream OK @ ${W}x${H} RGB3 (bgr24 interpretieren)."

# 8) Optionale Preview über Pipe (robust, kein direkter v4l2src)
if [[ "$PREVIEW" -eq 1 ]]; then
  command -v ffplay >/dev/null 2>&1 || die "ffplay fehlt (sudo apt install ffmpeg)."
  log "Preview – <q> beendet."
  exec sudo v4l2-ctl -d "$VID" --stream-mmap=4 --stream-to=- --stream-count=0 2>/dev/null | \
       ffplay -hide_banner -loglevel warning -fflags nobuffer -flags low_delay \
              -f rawvideo -pixel_format bgr24 -video_size ${W}x${H} -framerate 60 -i -
fi

log "Fertig. Device: $VID  Format: RGB3  (in Apps als bgr24 behandeln)."
