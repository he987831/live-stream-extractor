import requests
import json
import time
from flask import Flask, Response, jsonify
import threading

app = Flask(__name__)

# 全局变量存储直播源数据
live_sources = []
last_update_time = 0
update_interval = 300  # 5分钟更新一次

def fetch_live_sources():
    """从API获取直播源数据"""
    global live_sources, last_update_time
    
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'User-Agent': 'okhttp-okgo/jeasonlzy',
        'Connection': 'keep-alive',
        'referer': 'https://02utb8.55ffsgi.xyz',
        'getModel': 'SM-F7210',
        'getAndroidID': '1c8df037c224583a',
        'getUniqueDeviceId': '2cd9ca3c8897c3574aaf0d16edcd4a0f3',
        'getSDKVersionCode': '10',
        'getNetworkOperatorName': 'TelKila',
        'oaid': '',
        'uid': '-9999',
        'Host': 'sohg82.55ffsgi.xyz',
        'Accept-Encoding': 'gzip',
        'Cookie': 'PHPSESSID=6i06af5rvg9blg5smjrhfvh7lc'
    }
    
    try:
        response = requests.get(
            'http://sohg82.55ffsgi.xyz/appapi/?service=Home.getHot&uid=-9999&p=1&oaid=',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ret') == 200 and 'data' in data and 'info' in data['data']:
                live_sources = []
                for info in data['data']['info']:
                    if 'list' in info:
                        for stream in info['list']:
                            if 'pull' in stream:
                                # 提取RTMP直播流地址
                                live_sources.append({
                                    'title': stream.get('title', '未知标题'),
                                    'stream_url': stream['pull'],
                                    'viewers': stream.get('nums', '0'),
                                    'thumb': stream.get('thumb', ''),
                                    'avatar': stream.get('avatar', '')
                                })
                last_update_time = time.time()
                print(f"成功更新 {len(live_sources)} 个直播源")
    except Exception as e:
        print(f"获取直播源失败: {e}")

def update_loop():
    """后台更新循环"""
    while True:
        fetch_live_sources()
        time.sleep(update_interval)

@app.route('/')
def index():
    """显示可用的直播源列表"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>直播源列表</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            .stream { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
            .stream-title { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
            .stream-url { background: #f9f9f9; padding: 10px; border-radius: 3px; overflow-x: auto; font-family: monospace; }
            .copy-btn { background: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-top: 5px; }
            .last-update { color: #666; font-size: 14px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>直播源列表</h1>
            <p class="last-update">最后更新: <span id="update-time">""" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_update_time)) + """</span></p>
            <div id="streams">
    """
    
    for i, source in enumerate(live_sources):
        html += f"""
            <div class="stream">
                <div class="stream-title">{source['title']} (观众: {source['viewers']})</div>
                <div class="stream-url" id="url-{i}">{source['stream_url']}</div>
                <button class="copy-btn" onclick="copyUrl({i})">复制链接</button>
            </div>
        """
    
    html += """
            </div>
            <p><a href="/m3u">获取M3U播放列表</a> | <a href="/json">获取JSON数据</a></p>
        </div>
        <script>
            function copyUrl(index) {
                const urlElement = document.getElementById('url-' + index);
                navigator.clipboard.writeText(urlElement.textContent).then(() => {
                    alert('链接已复制到剪贴板');
                });
            }
            
            // 每60秒自动更新一次
            setInterval(() => {
                fetch('/json')
                    .then(response => response.json())
                    .then(data => {
                        if (data.length !== """ + str(len(live_sources)) + """) {
                            location.reload();
                        }
                    });
            }, 60000);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/m3u')
def m3u_playlist():
    """生成M3U播放列表"""
    m3u_content = "#EXTM3U\n"
    for source in live_sources:
        m3u_content += f"#EXTINF:-1, {source['title']}\n"
        m3u_content += f"{source['stream_url']}\n"
    
    return Response(
        m3u_content,
        mimetype="audio/x-mpegurl",
        headers={"Content-Disposition": "attachment;filename=live_streams.m3u"}
    )

@app.route('/json')
def json_api():
    """返回JSON格式的直播源数据"""
    return jsonify(live_sources)

@app.route('/update')
def manual_update():
    """手动触发更新"""
    fetch_live_sources()
    return jsonify({"status": "success", "count": len(live_sources)})

if __name__ == '__main__':
    # 启动时先获取一次数据
    fetch_live_sources()
    
    # 启动后台更新线程
    update_thread = threading.Thread(target=update_loop)
    update_thread.daemon = True
    update_thread.start()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=False)
