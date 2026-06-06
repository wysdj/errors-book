import os
os.system('taskkill /F /IM python.exe 2>nul')

# Read files
with open(r'D:\错题项目\services\static\app.js', 'r', encoding='utf-8') as f:
    js = f.read()

style = ''
try:
    with open(r'D:\错题项目\services\static\style.css', 'r', encoding='utf-8') as f:
        style = f.read()
except: pass

html = '''<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8">
<title>408 错题管理器</title>
<style>{style}</style>
</head>
<body>
<nav class="sidebar">
 <div class="logo"><span>📚</span>408 错题本</div>
 <a href="#" class="active" onclick="switchTab('capture',this)">📷 录入错题</a>
 <a href="#" onclick="switchTab('list',this)">📋 错题库</a>
 <a href="#" onclick="switchTab('stats',this)">📊 统计分析</a>
</nav>
<script>
{js}
</script>
</body></html>'''.format(js=js, style=style)

with open(r'D:\错题项目\services\static\index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Written', len(html), 'bytes')
print('Has switchTab:', 'function switchTab' in html)

# Start server
import subprocess
subprocess.Popen([r'D:\错题项目\services\.venv39\Scripts\python.exe', r'D:\错题项目\services\ocr_server.py'], 
                 cwd=r'D:\错题项目\services')
import time
time.sleep(4)
print('Server started')
