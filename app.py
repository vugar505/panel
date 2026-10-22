import os
from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# HTML səhifəsi birbaşa kodun içindədir (qovluq xətası verməz)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AzTube - Sosial Media Generator</title>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: #0b0f19; color: #fff; min-height: 100vh; overflow-x: hidden; }

        /* İNTRO EKRANI */
        #intro-screen {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, #0f172a, #1e1b4b, #311042);
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            z-index: 9999; transition: opacity 0.8s ease, visibility 0.8s ease;
        }
        #intro-screen.hide { opacity: 0; visibility: hidden; }
        .intro-logo { font-size: 3rem; font-weight: 800; background: linear-gradient(45deg, #a855f7, #ec4899, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: pulse 2s infinite; text-align: center; padding: 0 20px; }
        .intro-sub { margin-top: 15px; font-size: 1.1rem; color: #94a3b8; letter-spacing: 2px; }
        
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }

        /* ƏSAS KONTEYNER */
        .main-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; justify-content: center; }
        
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.5rem; background: linear-gradient(45deg, #c084fc, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
        .header p { color: #94a3b8; font-size: 1rem; }

        /* KART */
        .card { width: 100%; background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 35px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        
        .input-group { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
        .input-group input { flex: 1; min-width: 250px; padding: 16px 20px; background: rgba(15, 23, 42, 0.8); border: 2px solid #334155; border-radius: 14px; color: #fff; font-size: 1rem; outline: none; transition: 0.3s; }
        .input-group input:focus { border-color: #a855f7; box-shadow: 0 0 15px rgba(168, 85, 247, 0.3); }

        .btn { padding: 16px 30px; background: linear-gradient(135deg, #9333ea, #db2777); color: #fff; border: none; border-radius: 14px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(147, 51, 234, 0.4); }

        /* STATUS VƏ NƏTİCƏ */
        #status { text-align: center; margin-top: 20px; font-weight: 500; min-height: 30px; color: #cbd5e1; }
        .result-box { margin-top: 25px; padding: 20px; background: rgba(15, 23, 42, 0.9); border-radius: 14px; border: 1px solid #22c55e; display: none; text-align: center; }
        .download-btn { display: inline-block; margin-top: 15px; padding: 12px 25px; background: #22c55e; color: #fff; text-decoration: none; border-radius: 10px; font-weight: bold; transition: 0.3s; }
        .download-btn:hover { background: #16a34a; }

        /* YÜKLƏMƏ ANİMASİYASI */
        .spinner { width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; display: none; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <!-- İNTRO EKRANI -->
    <div id="intro-screen">
        <div class="intro-logo">AzTube Sosial Media Generator</div>
        <div class="intro-sub">Sistem Hazırlanır...</div>
    </div>

    <!-- ƏSAS SAYT -->
    <div class="main-container">
        <div class="header">
            <h1>AzTube Downloader</h1>
            <p>TikTok, YouTube və Instagram videolarını saniyələr içində yükləyin</p>
        </div>

        <div class="card">
            <div class="input-group">
                <input type="text" id="videoUrl" placeholder="Video linkini bura yapışdırın (TikTok, YouTube, Insta)...">
                <button class="btn" id="downloadBtn" onclick="startDownload()">
                    <span>Yüklə</span>
                    <div class="spinner" id="spinner"></div>
                </button>
            </div>

            <div id="status"></div>

            <div class="result-box" id="resultBox">
                <h3 id="videoTitle" style="margin-bottom: 10px; color: #fff;"></h3>
                <a id="downloadLink" href="#" class="download-btn" download>Faylı Cihaza Yüklə 📥</a>
            </div>
        </div>
    </div>

    <script>
        window.addEventListener('load', () => {
            setTimeout(() => {
                document.getElementById('intro-screen').classList.add('hide');
            }, 2000);
        });

        async function startDownload() {
            const url = document.getElementById('videoUrl').value.trim();
            const statusDiv = document.getElementById('status');
            const spinner = document.getElementById('spinner');
            const btnText = document.querySelector('#downloadBtn span');
            const resultBox = document.getElementById('resultBox');
            const downloadLink = document.getElementById('downloadLink');
            const videoTitle = document.getElementById('videoTitle');

            if (!url) {
                statusDiv.style.color = '#f87171';
                statusDiv.innerText = 'Zəhmət olmasa etibarlı link daxil edin!';
                return;
            }

            btnText.style.display = 'none';
            spinner.style.display = 'block';
            statusDiv.style.color = '#cbd5e1';
            statusDiv.innerText = 'Video serverdə emal olunur, zəhmət olmasa gözləyin...';
            resultBox.style.display = 'none';

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (response.ok) {
                    statusDiv.style.color = '#4ade80';
                    statusDiv.innerText = 'Video uğurla hazırdır!';
                    videoTitle.innerText = data.title;
                    downloadLink.href = data.download_url;
                    resultBox.style.display = 'block';
                    confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
                } else {
                    statusDiv.style.color = '#f87171';
                    statusDiv.innerText = data.error || 'Xəta baş verdi.';
                }
            } catch (err) {
                statusDiv.style.color = '#f87171';
                statusDiv.innerText = 'Serverlə əlaqə qurularkən xəta baş verdi.';
            } finally {
                btnText.style.display = 'inline';
                spinner.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Zəhmət olmasa video linki daxil edin!'}), 400

    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(id)s.%(ext)s'),
            'format': 'best',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base_name = os.path.basename(filename)

        return jsonify({
            'success': True,
            'download_url': f"/get-file/{base_name}",
            'title': info.get('title', 'Video')
        })
    except Exception as e:
        return jsonify({'error': f'Yükləmə xətası: {str(e)}'}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Fayl tapılmadı və ya silindi.", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
