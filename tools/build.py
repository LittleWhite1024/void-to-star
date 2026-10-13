"""把 src/ 下的源码打包成可直接游玩的单文件版本。

用法（在仓库根目录运行）：
    python tools/build.py 0.1

会生成：
    v0.1/index.html   这个版本的冻结副本，之后不再改动
    index.html        根目录入口，始终指向最新版本

背景音乐以 base64 内嵌进页面，所以单个 HTML 文件即可运行，
双击本地文件或放到 GitHub Pages 都能播放。
"""
import base64
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def build(version: str) -> str:
    src = (ROOT / 'src' / 'void-to-star.html').read_text(encoding='utf-8')
    b64 = base64.b64encode((ROOT / 'src' / 'bgm_loop.mp3').read_bytes()).decode()

    old = """      const res = await fetch('bgm_loop.mp3');
      if (!res.ok) return;
      const buf = await ac.decodeAudioData(await res.arrayBuffer());"""
    new = """      // 打包版：音乐内嵌在页面里，双击本地文件也能播放
      const bin = atob(document.getElementById('bgm-data').textContent.trim());
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      const buf = await ac.decodeAudioData(bytes.buffer);"""
    if old not in src:
        sys.exit('找不到音乐加载代码，src/void-to-star.html 的结构变了，请更新 build.py')
    src = src.replace(old, new)

    title = re.search(r'<title>.*?</title>', src).group(0)
    body = src.replace(title, '', 1)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="game-version" content="v{version}">
{title}
<style>html{{color-scheme:dark}}body{{margin:0;font:14px/1.5 system-ui,sans-serif}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
{body}
<script type="text/plain" id="bgm-data">{b64}</script>
</body>
</html>
"""


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('用法：python tools/build.py <版本号>，例如 python tools/build.py 0.1')
    ver = sys.argv[1].lstrip('v')
    html = build(ver)
    out = ROOT / f'v{ver}'
    out.mkdir(exist_ok=True)
    (out / 'index.html').write_text(html, encoding='utf-8')
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    print(f'已生成 v{ver}/index.html 和 index.html（{len(html) // 1024} KB）')
