# 免费工具优先：八平台下载路线（2026-11-06 核查）

## 选择原则

按用户最新要求：优先 GitHub 上可免费本机运行的下载工具，不使用收费聚合解析服务，移除龙猫下载入口。不要求每个后端本身都叫 Skill：本 Skill 负责调用它们的 CLI / 本地 API / MCP 并统一文件和验收。不要为了套一层 Skill 而引入收费远程 API Key。

当前已核对下列上游 README、支持范围、部分代码和许可证；**未安装和端到端实测所有新增后端，不能把候选路线称为八平台现已全部跑通**。它们主要取得平台发布的源视频，不能保证擦除作者本来烧进画面的标记；交付仍执行 [无水印复核规范](watermark-free-download.md)。

## 平台与首选后端

| 平台 | 优先免费本机工具 | 备用与实际边界 |
|---|---|---|
| 小红书 | [JoeanAmier/XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) | GPL-3.0；Python ≥3.12；有 CLI、本地 API、MCP。保留作品分享链接和 xsec_token，高清通常需 Cookie。备用 [lux](https://github.com/iawia002/lux)。原有 MediaCrawler 可在其许可范围内列清单与筛选。 |
| 抖音 | [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) | Apache-2.0；上游明确说明从平台干净流下载，并有本地 REST / MCP。新版包含数据库与身份池，需本机部署；不把作者的公开演示站当无限免费 API。已有 MediaCrawler 在其许可范围内可作轻量已有路径。 |
| 快手 | [JoeanAmier/KS-Downloader](https://github.com/JoeanAmier/KS-Downloader) | GPL-3.0；Python ≥3.12；支持作品链接、下载与本地 API。当前 README 的账号批量下载是未开放项，不把单条下载能力当主页全量采集。备用 lux；主页清单可保留已有 MediaCrawler。 |
| B站 | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 已有调用路径；备用 lux（MIT）或 [BBDown](https://github.com/nilaoda/BBDown)。高清取决于账号权限，合并音视频依赖 FFmpeg。 |
| YouTube | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 已有调用路径；需要时配置 Cookie、JavaScript 运行环境与可达网络。免费网站备用 cobalt → TubeDown。 |
| TikTok | [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的干净播放源格式 | 过滤 `download` / `download_addr` 与已标 watermarked 的格式，不能回退水印版。本地备用 Evil0ctal API；免费网站备用 cobalt → TikSave。 |
| Instagram | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 已有路径；网络、登录与限流可能影响结果。免费网站备用 cobalt。 |
| 微信视频号 | 现有 [ltaoo/wx_channels_download](https://github.com/ltaoo/wx_channels_download) + `wx_pipeline.py` | 源码可见、可免费本机使用；**许可证为 MIT + Commons Clause，不能描述成无限制的 MIT 开源项目**。本机抓取/解密需电脑微信、代理与证书。另有 [res-downloader](https://github.com/putyy/res-downloader) 本机嗅探备用；不声称单靠任意分享链接即可解析。 |

Facebook 不在原有八平台账号采集范围内；单链接下载可用 yt-dlp，免费网站备用 cobalt / FDown，不因此增加“九平台全量采集”的宣传。

## 获取及调用方式

只在实际选中的工具尚未安装时按其官方说明安装，先小样本验证。共享工具源码、虚拟环境、数据库和缓存放在用户指定的独立工具库，与项目平级；已有工具先复用，不重复下载。遵从用户的工程盘存放偏好，Skill 文件与配置保留原安装目录。每条任务的媒体、日志与复核证据留在该项目内。

1. **XHS-Downloader**：从上游完整克隆；`uv sync --no-dev` 安装基础依赖；启动 `uv run main.py api`，或按 README 安装 MCP 可选依赖后运行 `main.py mcp`。服务默认 `http://127.0.0.1:5556/docs`；`POST /xhs/detail` 接收 `url` 与 `download` 等字段，需要本地生成的 Bearer Token。当前官方说明“自动读取浏览器 Cookie”已失效，不据旧教程承诺自动取 Cookie。配置下载输出到项目待验目录或下载后归集；不把令牌打印到交付文档。
2. **抖音 API**：先读所拉版本的 README 和部署文件，按官方 `docker compose` 流程自托管。数据卷定向工具库/项目 E 盘；服务仅绑定本机，不在本任务中开放公网。通过实际启动后的 OpenAPI / MCP 工具表确定端点和字段，不沿用旧版 API 路径猜接口。尚未部署时记 `not_installed`，不冒充调用成功。
3. **KS-Downloader**：按 README 用 Python ≥3.12 / uv 安装并运行，首次检查 `--help` 和 API 文档；配置、输出位置按当前版本实际选项设置。本次只确认有下载与 API 能力，不捏造其尚未核实的 API 路径或账号列表能力。
4. **yt-dlp**：保留现有执行环境，检查版本和当前格式列表；YouTube、B站等可用 `bv*+ba/b` 合并完整视频。TikTok 使用无水印规范里的专门过滤，过滤只排除已知水印格式，不能代替视觉复核。音频从已验本地视频提取。
5. **lux**：官方 README 列出小红书、抖音、快手、B站等；MIT，可作为命令行备用。`lux -i <作品URL>` 先探测，`lux -o <项目待验目录绝对路径> <作品URL>` 下载。源码中的快手提取器仍基于页面 `photoUrl`，有适配失效风险；上游支持表不是本机成功实测，不承诺能跳过风控或保证无水印。
6. **视频号**：复用现有工具与已验证配置，不额外装重复的 Skill。只有现有工具失效才考虑 res-downloader 本机嗅探；它需操作系统代理/证书并在电脑端播放。使用前记录并在结束后恢复此次更改的代理状态。视频号 wrapper Skill 可能包含自动发微信/飞书操作，本任务只下载到本地，不因此开启转发。

## 免费与许可核查结果

- XHS-Downloader、KS-Downloader：GPL-3.0；免费本机运行。分发其修改或嵌入代码时遵循许可证，本仓库只链接和调用独立工具，不复制上游源码。
- Evil0ctal API：Apache-2.0。免费软件不等于远程托管、网络、代理或服务器资源永久免费。
- yt-dlp：官方源码使用 Unlicense；部分打包版本和依赖有独立许可，按实际分发包说明处理。
- lux：MIT。
- [MediaCrawler 许可证](https://github.com/NanmiCoder/MediaCrawler/blob/main/LICENSE)：非商业学习许可证 1.1；不能宣称可自由用于商业项目。已有批量路径保留其限制，商业用途不默认推荐它。
- [wx_channels_download 许可证](https://github.com/ltaoo/wx_channels_download/blob/main/LICENSE)：MIT 附加 Commons Clause，限制靠该软件功能向第三方收费提供产品/服务；不能写成无限制 MIT。
- res-downloader：GitHub 元数据为 Apache-2.0，但 README 另写仅学习研究、禁商业；存在说明差异，暂只作研究备用，不宣传为商业无限制工具。
- 不选要求商业远程 API Key / 付费额度的下载 Skill 作为“纯免费”后端。JoeanAmier/TikTokDownloader 可作为研究候选，但当前上游说明签名算法不再维护，不以它作为无需适配即可稳定工作的唯一抖音下载器。

执行前记录选中工具的版本/commit、许可证与小样本结果。仅查 README 或 `--help` 的状态写 `documented` / `cli_checked`，真实下载且经过画面复核后才可写 `download_verified` / `watermark_review_passed`。
