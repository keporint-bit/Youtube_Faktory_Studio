# robot_master.py → VERSIÓN INMUNE A TODO (última vez)
import os
import subprocess
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_NAME = "Canales_Youtube_2025"          # ← TU NOMBRE EXACTO
BASE = r"C:\YouTubeNoiseStudio"
FONDOS = os.path.join(BASE, "backgrounds")
SONIDOS = os.path.join(BASE, "real_sounds")
SALIDA = os.path.join(BASE, "upload_ready")
THUMBS = os.path.join(BASE, "thumbnails")
os.makedirs(SALIDA, exist_ok=True)
os.makedirs(THUMBS, exist_ok=True)

# Conectar Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json(creds_dict, scope)
client = gspread.authorize(creds)
book = client.open(SPREADSHEET_NAME)

# Buscar próxima fila PENDIENTE
fila = None
hoja = None
for ws in book.worksheets():
    datos = ws.get_all_values()
    for i, row in enumerate(datos[1:], 2):
        if len(row) >= 9 and row[8].strip().upper() == "PENDIENTE":
            fila = i
            hoja = ws
            data = row[:9] + [""]*(9-len(row))
            break
    if fila: break
if not fila:
    print("¡No hay más vídeos pendientes!")
    exit()

fecha, canal, fondo, audio, titulo, descripcion, thumb, hashtags, _ = data

fondo_path = os.path.join(FONDOS, fondo.strip())
audio_path = os.path.join(SONIDOS, audio.strip())
video_out  = os.path.join(SALIDA, f"[{canal}] {titulo}.mp4")
thumb_path = os.path.join(THUMBS, thumb.strip())
txt_path   = os.path.join(SALIDA, f"[{canal}] {titulo}.txt")

# VERIFICAR QUE EXISTAN LOS ARCHIVOS
if not os.path.exists(fondo_path):
    print(f"ERROR: No existe el fondo → {fondo}")
    exit()
if not os.path.exists(audio_path):
    print(f"ERROR: No existe el audio → {audio}")
    exit()

print(f"Generando → {canal} | {titulo}")

cmd = (
    f'ffmpeg -y -stream_loop -1 -i "{fondo_path}" '
    f'-stream_loop -1 -i "{audio_path}" '
    f'-vf "zoompan=z=\'min(zoom+0.0015,1.5)\':d=750:s=1920x1080:fps=30,format=yuv420p" '
    f'-c:v libx264 -preset ultrafast -crf 23 -c:a aac -b:a 192k '
    f'-t 36000 -movflags +faststart "{video_out}"'
)
subprocess.run(cmd, shell=True, check=True)

# Thumbnail opcional
if os.path.exists(thumb_path):
    tmp = video_out.replace(".mp4", "_tmp.mp4")
    subprocess.run(f'ffmpeg -i "{video_out}" -i "{thumb_path}" -map 0 -map 1 -c copy -disposition:v:1 attached_pic "{tmp}"', shell=True)
    os.replace(tmp, video_out)

# .txt
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(titulo + "\n\n" + descripcion + "\n\n" + hashtags)

# Solo marcar GENERADO si todo salió bien
hoja.update_cell(fila, 9, "GENERADO")

print(f"\n¡100% TERMINADO! → {video_out}")
os.startfile(SALIDA)
