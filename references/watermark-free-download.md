# 无水印下载与交付验收（2026-11-06）

## 交付要求

本 Skill 下载的视频必须无水印：包括平台标志、移动账号 ID、片头片尾下载水印、下载站新增标记，以及作者烧进画面的水印/Logo。普通内容字幕不自动判为水印。不能确认性质的标记记为 `uncertain`，不能交付。优先获取原始无水印源；发现水印就换源。不能通过裁切、模糊、遮盖或生成式擦除来冒充无水印原片。

这些网站不能保证擦除作者已烧录的标记。找不到干净来源时保留失败记录，报告未完成；不得回退为带水印版本、音频文件或缩短的片段。无水印不改变原作品的授权范围。

## 免费工具优先与网站备用

用户最新要求优先使用免费本机工具，执行 [八平台免费工具路线](open-source-downloaders.md)。龙猫因收费已从下载路由移除；不自动购买、注册付费套餐或以其他收费聚合 API 代替。

下表保留四个免费网站的网页备用流程，**不是四个已经实现并实测通过的 Python API 适配器**。每次使用前核实当前页面、平台支持、登录及费用条件；若出现收费要求跳过。2026-11-06 仅检查公开说明，未用四站完成真实视频下载。

| 网站 | 用途与路由 | 操作与边界 |
|---|---|---|
| [TikSave](https://tiksave.io/zh-cn) | TikTok 网页备用源；官网说明提供免费无水印 MP4 | 粘贴原作品链接 → 下载 → 选无水印 MP4；不能把 MP3 当作视频。官网声称无水印仍须复核实际文件。 |
| [cobalt](https://cobalt.tools/) | TikTok、YouTube、Instagram、B站等备用；Facebook 仅限公开可访问作品 | 粘贴单作品链接 → 视频/auto 模式 → 确认不选带水印选项 → 下载。服务是否开启以当前实例为准；不能把 TikTok 支持套用于抖音。 |
| [TubeDown](https://tubedown.cn/youtube) | YouTube 网页备用入口 | 粘贴 YouTube 作品链接 → 解析视频 → 选完整高清视频；核对音视频、时长与清晰度。该页没有承诺擦除画面内已有 Logo。 |
| [FDown](https://fdown.net/) | Facebook 视频/Reels 备用入口 | 粘贴 Facebook 视频链接 → Download → 选实际可用完整高清版本。它不是通用八平台解析器；Facebook 这里只新增单链接下载备用，不宣称新增账号全量采集。 |

cobalt 的支持范围见[官方服务表](https://github.com/imputnet/cobalt/blob/main/api/README.md)。[官方 API 文档](https://github.com/imputnet/cobalt/blob/main/docs/api.md)说明托管 API 有机器人防护，需实例方授权或自建实例；不要把 `api.cobalt.tools` 硬编码成免费批量接口。现阶段使用网页入口；以后确需 API 时再配置已获准的实例。

## 按平台执行

1. 先按平台参考列清单、筛选，不改变原筛选条件。原平台直链、MediaCrawler 或 yt-dlp 能取得干净源时先用它。
2. TikTok 不使用 `download` / `download_addr` 作为兜底；这些可能带平台水印。先列出真实格式，排除已标为 watermarked 的项，再选播放源格式。本机路线失败后切 cobalt → TikSave，不降级带水印。
3. YouTube：yt-dlp → cobalt → TubeDown；Instagram：yt-dlp → cobalt；B站：yt-dlp / lux → cobalt；Facebook 单作品：yt-dlp → cobalt → FDown。
4. 小红书：XHS-Downloader → lux；抖音：本机 Evil0ctal API / 已有许可适用的 MediaCrawler；快手：KS-Downloader → lux；视频号：现有专用工具 → 本机嗅探备用。细节及许可证见免费工具路线，不假定四个海外网站支持这些国内平台。
5. 每站同一作品最多一次正常尝试和一次合理重试，之后换下一个适配源。依赖登录、验证码或付费且当前无法完成时记录原因，继续其他来源；这些情况不计成功。不要硬猜解析 API、复制会话 Cookie 给下载站，或安装站点推荐的扩展/可执行程序。
6. 每次换源核对作品 ID、作者、标题、画面与时长；使用原作品链接。下载到项目的 `01_过程稿_临时资料/无水印待验/`，不要直接写正式素材目录。网页默认下载落到别处时，确认完整文件后归集到该目录。

查看适配网页备用入口：

```powershell
python scripts/verify_watermark_free.py plan --platform tiktok
```

浏览器自动化可完成网页提交、选格式和下载；具体按钮从当次页面读取。无浏览器工具、页面失效或解析失败时如实记录 `unavailable`，不要把列出网站写成“自动下载成功”。

## TikTok 与音频

先运行 `yt-dlp -F <作品URL>` 检查实际格式；适用时选择排除已知带水印格式的源：

```powershell
yt-dlp --no-playlist --write-info-json -f 'best[ext=mp4][format_id!*=download][format_note!*=?watermarked]/best[format_id!*=download][format_note!*=?watermarked]' -o '<待验目录绝对路径>/%(id)s.%(ext)s' '<作品URL>'
```

格式过滤只排除已知标记，不能证明画面无水印。代理、Cookie 和 impersonate 按本机已验证配置追加；格式不存在就换网站。根据真实容器使用对应后缀，不能只把 WebM/FLV 重命名为 MP4。需要 MP4 时正确封装/转码后对最终文件重新验收。

视频通过验收后从**同一个已验视频**提取 M4A，避免重新请求视频 URL 取得另一版本：

```powershell
ffmpeg -i '<已验视频绝对路径>' -vn -c:a aac '<同名音频绝对路径>.m4a'
```

若原作品确实无音轨，如实记录，不制造音频或当作下载损坏；保留完整视频。

## 验收、记录与正式归集

检查每条视频身份、完整性、时长、清晰度与音轨。逐条全片播放/审看，关注四角、中央、片头、片尾及移动/间歇水印。抽帧/OCR只能辅助定位，不能单凭若干帧、文件名或“无水印”按钮判定全片通过。无法全片复核的文件保持 `pending`/`uncertain`；不得填写虚假的复核记录或要求用户批准后冒充技术保证。

复核由有视频审看能力的 Agent 或实际审看者完成；记录方式不限制必须由用户手动填写。若宿主无法审看，应报告这项能力缺失，继续完成可执行的下载与登记。

1. 以**筛选命中总数**登记；不是“下载成功数”。新文件默认 `pending`，重新登记同名但内容变化的文件会重置为待验。

   ```powershell
   python scripts/verify_watermark_free.py init '<项目根绝对路径>' --platform tiktok --expected-count 9
   ```

2. 完成全片复核后，在项目内保存真实复核记录（Markdown），写明文件名、SHA-256、原作品 URL、下载来源、画面检查、时长/音轨检查及结论。在 `01-视频清单/watermark_review.json` 对应条目填写：`source_url`、`provider`、真实 `format_id` / `format_note`（可获取时）、`watermark_status`（`clean` / `watermarked` / `uncertain` / `pending`）、`full_video_reviewed`、`reviewer`、`review_notes` 和 `evidence`（项目内复核记录相对路径）。只有实际全片复核且无任何水印才填 `clean` 和 `true`；SHA 由脚本生成，不手填假值。
3. 运行 `check '<项目根>' --staging`。脚本核对条数、逐文件 SHA、复核记录、有效视频流与时长；**脚本不执行视觉水印识别**，不会自动把待验改为通过。
4. 全部通过后运行 `promote '<项目根>'`，将已验视频复制到 `02-Whisper转写/视频源文件/`；不会覆盖不同内容的旧文件。
5. 转写与最终交付前运行 `check '<项目根>'`。缺失/多余/替换文件、空清单、未复核、有水印或无法确认均以非零退出。部分成功只报告通过数与失败原因，整体任务仍为未完成，不删失败项来伪造全通过。

`wx_pipeline.py` 已接入此检查：下载进待验目录后会暂停；复核与 promote 完成，再用相同参数加 `--skip-download` 续跑。`transcribe_with_whisper.py` 也在加载模型前检查正式素材。把脚本复制进项目时同时复制 `verify_watermark_free.py`。独立调用其他转写器，也必须先执行此检查。

旧版平台文档里的“下载完成”仅表示已取得候选文件。本文件与入口 Skill 的无水印要求优先；旧项目已存在的文件也不能免检。
