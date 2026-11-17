# 创建与检查项目环境

先检查项目已有 `.venv`、`pyproject.toml`、requirements 和锁文件。以下命令在目标项目目录执行，`/path/to/iv8` 替换为当前 skill 的绝对目录。不要用另一个业务项目的虚拟环境作为正式环境。

## 选择解释器

2026-11-17 核对的[上游说明](https://github.com/HanZzzzz000/iv8)：Windows x64、Linux x64/aarch64 支持 Python 3.9–3.14；macOS 预编译 wheel 自 0.1.4 起支持 Python 3.11–3.14、macOS 14+、arm64/x86_64。新项目优先 Python 3.12；使用前核对当前 PyPI wheel 的 Python ABI、CPU 和系统最低版本，不能只按这份历史范围推断兼容。

```sh
python3 -c 'import sys,platform; print(sys.executable); print(sys.version); print(platform.system(), platform.release(), platform.machine())'
```

Windows 可用 `py -0p` 查解释器。macOS 自带 Python 3.9 即使存在也不匹配上述 macOS wheel。

## 已有 uv：创建项目虚拟环境

只在 `.venv` 不存在时运行创建命令；新建名称不得覆盖已存在的环境。缺少 Python 3.12 时引导执行 `uv python install 3.12`，说明这会下载解释器；在已有授权范围内可直接执行。没有 uv 时走下方 venv 分支，无须为了使用 iv8 额外安装 uv。

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python iv8 --index-url https://pypi.org/simple
.venv/bin/python /path/to/iv8/scripts/check_environment.py
```

Windows PowerShell 中解释器路径使用 `.venv\Scripts\python.exe`：

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe iv8 --index-url https://pypi.org/simple
.venv\Scripts\python.exe C:\path\to\iv8\scripts\check_environment.py
```

已有 uv 项目按项目约定使用 `uv add iv8` / `uv sync`，保留原锁文件和版本约束，不将临时安装成功当成依赖已记录。

## 没有 uv：标准 venv

macOS/Linux，确认 `python3.12` 可用后：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install iv8 --index-url https://pypi.org/simple
.venv/bin/python /path/to/iv8/scripts/check_environment.py
```

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install iv8 --index-url https://pypi.org/simple
.venv\Scripts\python.exe C:\path\to\iv8\scripts\check_environment.py
```

若系统没有合适的 Python，先说明检测到的平台/版本和缺口，提供官方 Python 安装入口或机器上已有包管理器的准确安装命令。系统软件安装需要用户操作时，停在该依赖步骤，用户完成后重新检查；不能声称环境已建好。Linux 若缺 `venv` 模块，按实际发行版引导安装相应 venv 包，不套用其它系统命令。

## 按任务增加依赖并记录版本

独立 HTTP 示例为 `httpx[http2]`；只有确实需要 HTTP/2 时安装相应 extra。HTML 解析、PySide6 GUI、浏览器自动化不是 iv8 的基础依赖，不默认一起装。

先让 smoke probe 通过，再将实际验证版本及直接依赖记录到项目现有依赖文件/锁文件。历史案例使用 iv8 0.1.4；复现该案例可在独立实验环境安装 `iv8==0.1.4`，新项目不自动固定历史版本，也不自动升级已有生产依赖。

## 排障

- `No matching distribution`：核对 CPython ABI、架构、macOS 最低版本、官方源和所需版本的 wheel；不要把不匹配的 wheel 改名强装，也不要因安装失败自动开始源码编译。
- `ModuleNotFoundError`：用同一个绝对解释器路径运行 `-m pip show iv8` 和探针，排除终端激活环境与实际进程不一致。
- 下载超时：先检查代理/证书/网络，uv 可设置 `UV_HTTP_TIMEOUT=300`；从官方 PyPI 文件服务下载匹配 wheel 时核对 SHA256，不禁用 TLS 校验、不转向不明镜像。离线机器引导在同平台兼容机器下载 wheel，再本地安装。
- import/原生库加载失败：记录版本、ABI、架构和错误类型，检查动态库和系统版本。探针失败不反复请求业务网站。
- 目标脚本报 DOM/旧版 jQuery 递归错误：缩到最小函数与依赖，基础 probe 通过不代表整页兼容。
- `__iv8__` 的 `typeof` 可能特意表现为 undefined；直接按上游文档调用所需方法，不能因此判定工具对象不存在。

## 实测兼容性提醒

本机 iv8 0.1.4 的 `new URLSearchParams({q:"a b+c"}).toString()` 返回 `q=a b+c`，标准期望为 `q=a+b%2Bc`。探针会将 `form_encoding` 标记失败并退出 1，这不是漏装依赖。其它 API 通过也不能掩盖该项差异；若目标依赖表单编码，应使用宿主标准编码器并对照实际浏览器请求，或验证其它版本/最小补丁。与该 API 无关的目标函数可在明确记录限制后单独验证，无须因一项差异反复重装环境。
