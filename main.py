from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
import os
import subprocess
import uuid
import openai
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do FastAPI
app = FastAPI(title="API de Integração com OpenAI")

# Montar a pasta 'static' para servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Diretório para salvar os arquivos de upload
UPLOAD_DIR = "uploads"
AUDIO_DIR = os.path.join(UPLOAD_DIR, "audios")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Defina sua chave de API da OpenAI de forma segura
openai.api_key = 'sua_chave_de_api_aqui'

# Rota para servir o arquivo HTML
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", encoding='utf-8') as f:
        return f.read()

# Modelo de entrada para a rota de download de áudio
class VideoURL(BaseModel):
    url: str

@app.post("/download-audio/")
async def download_audio(video: VideoURL):
    """
    Recebe uma URL de vídeo do YouTube, baixa o vídeo em MP4,
    extrai o áudio e salva como MP3.
    """
    video_url = video.url

    try:
        # Gerar um ID único para evitar conflitos de nomes
        file_id = str(uuid.uuid4())

        # Opções do yt-dlp para baixar o vídeo como MP4
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{file_id}_%(title)s.%(ext)s",
            'restrictfilenames': True,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        # Baixar o áudio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_filename = ydl.prepare_filename(info_dict)

        # Definir o caminho do arquivo de áudio
        audio_filename = f"{file_id}_audio.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        # Converter para MP3 se necessário
        if not video_filename.endswith('.mp3'):
            # Comando FFmpeg para converter para MP3
            comando_ffmpeg = [
                "ffmpeg",
                "-i", video_filename,
                "-vn",
                "-ab", "192k",
                "-ar", "44100",
                "-y",
                audio_path
            ]

            # Executar o comando FFmpeg
            resultado = subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if resultado.returncode != 0:
                # Remover o arquivo baixado se ocorrer um erro na conversão
                os.remove(video_filename)
                erro = resultado.stderr.decode()
                raise HTTPException(status_code=500, detail=f"Erro ao converter áudio: {erro}")

            # Remover o arquivo original após a conversão
            os.remove(video_filename)
        else:
            # Se já for MP3, mover para o diretório de áudios
            os.rename(video_filename, audio_path)

        return JSONResponse(content={
            "message": "Áudio extraído com sucesso.",
            "audio_path": audio_path
        }, status_code=200)

    except yt_dlp.utils.DownloadError as de:
        erro = str(de)
        raise HTTPException(status_code=400, detail=f"Erro ao baixar o vídeo: {erro}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
