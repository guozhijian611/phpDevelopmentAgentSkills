# SaiStore 登录与插件上传

适用于用户明确要求操作 SaiThink 开发者后台。它与本地 SaiAdmin 的插件 ZIP 导入是两个目标；不能把本地 admin 账号发送到商店，也不能在用户只要求开发/打包时自动发布。协议证据见 [接口核对记录](saistore-protocol.json)。

## 登录与本地会话

脚本仅依赖 Python 3.9+ 标准库，可从任意目录运行。下列相对路径以 skill 根目录为起点；全局选项放在子命令之前：

```sh
python3 scripts/saistore.py --help
# 当前已核对站点为 HTTP；该选项明确接受账号/令牌明文传输风险
python3 scripts/saistore.py --allow-http auth login
python3 scripts/saistore.py auth status
python3 scripts/saistore.py --allow-http apps list
```

登录会在交互终端提示用户名，获取 UUID/验证码图片并尝试打开图片，用户输入验证码后通过 getpass 隐藏输入密码。输入 r 获取新验证码，q 取消；登录失败仅在用户明确选择重试时获取新挑战，单次最多三轮。`--no-open-captcha` 仅显示私有临时图片路径供用户自行查看。不会读验证码响应中的 result 来作答，不做 OCR，不绕过验证。非 TTY 环境拒绝读取密码；AI 应给出上述命令，用户自行在本机终端输入，不在聊天或命令参数中传递秘密。

成功后 access_token 与 refresh_token 成对原子写入：

```text
${XDG_CONFIG_HOME:-~/.config}/saiadmin6-plugin/saistore/<API地址哈希>.json
```

按 POSIX 目录 0700、文件 0600 管理（Windows 须核对对应 ACL）。缓存绑定完整 API 地址，拒绝跨站使用或符号链接、权限过宽的状态文件。只保存账号标识、令牌、时间与目标，不保存密码；status 只显示是否存在和有效期提示，不输出令牌。`--config-dir` 可指定私有目录，实际使用不得放入 Git 工作区；测试只能使用一次性临时目录。

访问令牌有效时直接复用；已过期或只读请求明确返回 401 时，在交互终端重新登录一次，非交互命令提示先登录。当前前端保存 refresh_token 但未调用刷新接口，未取得可以核对的服务端刷新路由；因此本版保存它但不猜测自动刷新。JWT exp 仅作为本地过期提示，服务端授权仍是事实源。

```sh
# 仅删除该站点本地令牌，不声称服务端已撤销会话；保留上传回执
python3 scripts/saistore.py auth logout
```

## HTTP 与 HTTPS 的实际边界

2026-11-16 核对：用户提供的后台为 `http://manage.saithink.top`，API 前缀为 `/prod`；HTTPS 连接存在证书主机名不匹配。脚本不使用 verify=False、不自动降级、不跟随 API 重定向，不将令牌转发到其它站点。只有显式 --allow-http 才发送 HTTP 请求。站点修复可信证书后可用 `--base-url https://manage.saithink.top/prod`；不同地址使用独立缓存，不自动搬移旧令牌。示例中的 HTTP 选项不是推荐生产传输方式。

## 应用资料与图片

已有应用先 `apps list` 找 ID，再 `apps read --app-id ID`。新应用必须具备名称、标识、简介、类型、图标、截图、支持版本、价格与 Markdown 内容，清单示例见 [app.example.json](../assets/saistore/app.example.json)。不要把示例占位资源实际提交到商店。

图片可通过已核对的核心上传接口上传（小于 5 MiB 的 PNG/JPEG/GIF/WebP，先核对用户授权的文件）：

```sh
python3 scripts/saistore.py asset-upload --file /path/to/logo.png --dry-run
python3 scripts/saistore.py --allow-http asset-upload --file /path/to/logo.png
```

输出私有 asset_ref 文件路径，不把可能含签名参数的资源地址打印到日志。应用清单 logo、screenshots 可使用既有 HTTP(S) 图片 URL，也可引用 `{"asset_ref":"/path/to/image-receipt.json"}`；图片回执必须来自同一 API 站点。支持版本的实际选项中 `2` 对应 saiadmin 6.x，清单使用 `"support":["2"]`，不要把 info.ini 的 `6.x` 直接当作商店字典值。

```sh
python3 scripts/saistore.py apps create --manifest /path/to/app.json --dry-run
python3 scripts/saistore.py --allow-http apps create --manifest /path/to/app.json
python3 scripts/saistore.py --allow-http apps list --keywords example
```

创建前检查是否已有同标识应用，不重复创建或覆盖。创建应用不提交审核。脚本只覆盖已核对的字段，不擅自修改销售条款、价格或其它用户资料；价格和内容由用户的清单提供。

## 上传最终插件版本

先完成本 skill 的本地/双库/浏览器适用验收，只使用同一份最终 ZIP。CLI 再检查 ZIP 根元数据、6.x 支持、三段版本号、插件目录所有权、CRC、重复条目、越界/符号链接、环境凭据路径与体积。默认按后台控件限制 ZIP 小于 10 MiB；其它前端目录可传 --frontend，不盲目突破服务器约束。

```sh
python3 scripts/saistore.py upload --zip /path/to/example-1.2.3.zip \
  --app-id 9 --notes-file /path/to/changes.md --kind fix --dry-run
python3 scripts/saistore.py --allow-http upload --zip /path/to/example-1.2.3.zip \
  --app-id 9 --notes-file /path/to/changes.md --kind fix
```

真实流程为：登录/会话 → 读取自己可访问的应用，核对 appname → 检查重复版本 → multipart 字段 file 上传 ZIP → addVersion 写入 app_id/version/type/remark/file_path/status → versionList 读回确认。版本类型 major=1、feature=2、fix=3；上传不会调用 submitReview，也不代表审核通过。

本地回执位于私有配置目录的 receipts，绑定 API、应用 ID、appname、ZIP SHA256 和版本。文件地址与阶段只在回执内保存。超时或断连时不自动重复写入：

- 已上传文件、版本创建失败：核对回执及远端版本，显式 --resume 复用地址，不重复上传文件。
- 远端已有同版本且与该回执 file_path 一致：--resume 只读确认并补记完成。
- 上传本身结果未知、没有可确认地址：停止，先在后台核对资源，不能猜测重放或自动删除远端文件。
- 没有该回执的同版本：拒绝覆盖，不把版本号相同当作包内容相同。

## 提交审核独立执行

只有用户明确要求提交审核时才运行，先核对应用 ID 与当前状态：

```sh
python3 scripts/saistore.py submit-review --app-id 9 --dry-run
python3 scripts/saistore.py --allow-http submit-review --app-id 9
```

仅草稿状态提交一次，并读回待审核状态；其它状态拒绝重复提交。待审核不等于已上架/已通过，不自动更改审核结果、销售或财务设置。

## 验证范围

本轮已实测公开验证码接口，观察已登录浏览器中的应用列表请求与新增表单，核对公开前端资源中的登录、上传、版本和审核路径/字段。未使用真实密码测试 CLI 登录，也未创建或上传任何真实商店应用。

`python3 tests/test_saistore.py` 使用本地 HTTP 夹具覆盖手工验证码与 cookie、密码不保存/错误脱敏、令牌配对/权限/站点绑定、HTTP 拒绝与重定向拒绝、包预检、multipart、版本读回、重复拒绝、断点恢复、图片回执和审核分离。该测试不代替官方后台的真实账号权限、上传和审核验收；遇到接口变化停止并重新核对，不伪造成功。
