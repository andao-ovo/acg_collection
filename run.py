#!/usr/bin/env python3
"""
ACG收藏馆 —— 一键启动

同时提供后端 API 和已构建好的前端页面，全部在同一个端口上：

    网页首页   http://127.0.0.1:8000/
    接口文档   http://127.0.0.1:8000/docs

用法：
    python run.py                  # 默认绑定 127.0.0.1:8000
    python run.py --port 9000      # 换端口
    python run.py --host 0.0.0.0   # 允许局域网内其他设备访问

Redis 是可选的，没有安装或没有运行都不影响启动。
"""

import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_INDEX = ROOT / "frontend" / "dist" / "index.html"


def _get_option(args, name, default):
    """从命令行参数里取 --name value 形式的值。"""
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        return None
    return args[index + 1]


def _port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main():
    # 输出被重定向到文件/管道时，print 默认是块缓冲的，日志会迟迟不出现。
    # 改成行缓冲，保证启动信息和降级提示能实时看到。
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:      # Python 3.6 及更早没有 reconfigure
        pass

    # 保证无论从哪里调用，模块导入路径都以项目根目录为准
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    args = sys.argv[1:]

    port = _get_option(args, "--port", 8000)
    if port is None:
        print("错误：--port 后面需要一个端口号，例如  python run.py --port 9000")
        return 1
    try:
        port = int(port)
    except (TypeError, ValueError):
        print("错误：端口号必须是整数，收到的是 %r" % (port,))
        return 1

    host = _get_option(args, "--host", "127.0.0.1")
    if host is None:
        print("错误：--host 后面需要一个地址，例如  python run.py --host 0.0.0.0")
        return 1

    if not DIST_INDEX.is_file():
        print("错误：没有找到前端构建产物")
        print("      %s" % DIST_INDEX)
        print()
        print("  请先构建一次前端（需要 Node.js，只需执行一次）：")
        print("      cd frontend")
        print("      npm install")
        print("      npm run build")
        return 1

    if _port_in_use(port):
        print("错误：端口 %d 已被占用（可能是上一次启动的服务还开着）。" % port)
        print("      换个端口试试： python run.py --port 8001")
        return 1

    import uvicorn

    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print("=" * 58)
    print("  ACG收藏馆 启动中 ...")
    print("=" * 58)
    print("  网页首页    http://%s:%d/" % (display_host, port))
    print("  接口文档    http://%s:%d/docs" % (display_host, port))
    print()
    print("  按 Ctrl+C 停止服务")
    print("=" * 58)
    print()

    uvicorn.run("main:app", host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
