# RELEASE_STRATEGY.md — TokenAPI Scan 公开发布策略

> **状态:** v0.1 草案 (2026-06-26)
> **结论先行:** 本文档是**发布前必读**,GitHub 推送/Release 在本策略走完之前**全部冻结**。
> **关联:** `BRAND_INDEPENDENCE_AND_OSS_POLICY.md`(三层分级源头)·`AGENT_API_CONTRACT.md`(API 兼容性)·`DATA_LINEAGE.md`(数据治理)。

---

## 0. 为什么需要这份文档

当前实测状态 (2026-06-26):

1. **本地生产仓** `/home/debian/tokenscan_v2` —— **无 git remote**,本地单一真相源,203 个未提交改动。
2. **公开门面仓** `github.com/TokenScanAI/tokenapi-scan` —— 已在 README/llms.txt/base.html footer 指向,但**当前内容陈旧**(canarybyte/tokenapi-scan 时代遗留)。
3. **三层资产** 已由 `BRAND_INDEPENDENCE_AND_OSS_POLICY.md` 划清:
   - Layer 1(公开 MIT):API 契约 / SDK / 数据字典 / 检测方法论概述
   - Layer 2(受控开源):公开规范文档 + 闭源实现
   - Layer 3(永久闭源):检测内核 / 反作弊判据 / 爬取节点 / 生产数据

**没有写死的事**(本文档解决):
- 哪些文件能进门面仓、哪些**必须屏蔽**、灰色地带怎么人工 review
- 单仓 vs 多仓 vs subtree 选型
- 第一次发布前的安全 checklist(history / secrets / 内网 IP / TODO 标注)
- 持续发布流水线(生产→门面的单向同步,绝不反向)
- 版本号 / Release / CI 策略

---

## 1. 发布目标(写死)

### 1.1 门面仓承载什么(IN)

| 类别 | 示例 | License |
|---|---|---|
| **API 契约 + OpenAPI schema** | `docs/standards/AGENT_API_CONTRACT.md` + 自动生成的 `openapi.json`(v1 path 公开版) | MIT |
| **数据治理 / 字典 / 方法论概述** | `docs/standards/DATA_GOVERNANCE_FRAMEWORK.md` · `DATA_CATALOG.md` · `DATA_LINEAGE.md` · `MODEL_DATA_STANDARD.md` · `CATALOG_STANDARD.md` · `COLLISION_CLASSIFICATION_STANDARD.md` 等 | MIT |
| **品牌与开源政策** | `BRAND_INDEPENDENCE_AND_OSS_POLICY.md` · README · CONTRIBUTING · SECURITY · LICENSE | MIT |
| **Python 客户端 / MCP SDK 样板** | 未来 `clients/python/`,`clients/mcp/`(占位) | MIT |
| **检测原理白皮书(高层)** | `docs/standards/SYSTEM_DESIGN.md`(只到方法论层) | MIT |
| **示例数据** | 脱敏的 detection sample、价格对比 sample(CC-BY-NC 4.0) | CC-BY-NC 4.0 |

### 1.2 门面仓**绝不**承载什么(OUT)

| 类别 | 物理位置 | 原因 |
|---|---|---|
| **检测内核源码** | `src/relay_detector/protocols/`(L1/L2/L3 探测器全部) | Layer 3 红线 §2.4-1/2/5 |
| **反作弊 / 反爬规则** | `src/governance/` 中阈值与 heuristic | Layer 3 红线 §2.4-5 |
| **生产数据** | `web_data/db/*.db` · `web_data/jobs/` · `web_data/health/` · `web_data/seo_reports/` 等 | Layer 3,含真实 endpoint / 命中/打码 key 残片 |
| **爬虫 / 节点 / 代理** | `tools_dev/price_scraping/` · `~/.hermes/scripts/tokenapi_probe_candidates.py` · sing-box / clash 配置 | Layer 3 红线 §2.4-2/3 |
| **可执行 plan / 微信群路由** | `docs/plans/` · `.hermes/` · skill 全集 | 含运维秘密 + 个人偏好,不公开 |
| **任何 `.env` / API key / db / 备份 tar** | `.env*` · `*.db` · `*.tar.gz` · `*.bak.*` · `*backups/` | 安全红线 |
| **个人/内网信息** | `192.168.x.x` 内网 IP · `tui_handoff.md` · `/home/debian/...` 绝对路径 | 隐私 + 攻击面 |

### 1.3 灰色地带(逐文件人工 review)

| 文件类 | 决策提示 |
|---|---|
| `web/server.py` | **NOT IN** — 含路由逻辑、内网假设。门面仓只放 OpenAPI 衍生品。 |
| `web/templates/*.html` | **review** — 公开页面模板可放,内部 `/admin/*` 必去 |
| `scripts/governance/build_data_catalog.py` | **OK** — 治理脚本本身是 Layer 1 价值,且无凭据 |
| `tools_dev/visual_audit/*` | **review** — 多分辨率回归工具可放,内部 url 必参数化 |
| `tests/*` | **review** — mock 测试可放(已是 mocked 探测器),真实集成测试不放 |
| `pyproject.toml` / `requirements*.txt` | **OK** — 依赖清单可公开,但 `[tool.x.private]` 段必去 |
| `.github/workflows/test.yml` | **review** — 现有 CI 跑 mocked 测试,可保留;**禁出现** secret 或自托管 runner 引用 |

---

## 2. 仓库形态选型(决策)

### 2.1 候选

| 选项 | 描述 | 优 | 劣 |
|---|---|---|---|
| **A. 单仓 (monorepo) 公开 + 内部分支** | 一个 git,private 主分支 + public mirror 分支,filter-branch | 配置最简 | 一次推错全泄;history 难清 |
| **B. 双仓物理隔离 + 单向 sync 脚本** ✅ | 生产仓本地无 remote;门面仓单独干净仓,内容由 `tools_dev/release/sync_to_facade.py` 从生产取白名单文件 push | 物理隔离最强;每次推送可 diff;失误成本低 | 同步脚本要写,文档要双向引用 |
| **C. git subtree / submodule** | 生产仓内嵌门面仓 subtree | 单一开发流 | subtree push 要严格白名单,history 串味,Layer 边界容易破 |

**选 B**。理由:Layer 3 红线 §2.4-3「公开后是否泄漏正在使用的探测节点/资源/凭据」必须答「绝不」,B 是唯一能在物理上保证"生产仓任何 commit 都不会意外进公开历史"的方案。

### 2.2 物理布局(写死)

```
/home/debian/tokenscan_v2/                 # 生产仓 · 无 remote · Layer 1+2+3 全部
└── tools_dev/release/
    ├── sync_to_facade.py                   # 同步脚本(待建,§4)
    ├── facade_whitelist.yaml               # 白名单清单(逐文件)
    ├── facade_blacklist_patterns.yaml      # 全局黑名单 regex(secret/IP/路径)
    └── facade_workdir/                     # 临时工作目录(.gitignore)

/home/debian/tokenscan_facade/             # 门面仓 · 独立 git · remote = TokenScanAI/tokenapi-scan
    └── (sync_to_facade.py 写入,人工 review,git push)
```

**红线:**
- 生产仓**永远**`git remote -v` 输出为空(grep 校验进 daily watchdog,见 §6)
- 门面仓**永远**只从同步脚本进数据,**禁手 cherry-pick**

---

## 3. 文件白名单首版(供同步脚本读)

> **结构:** 路径 → license tag → 是否需脱敏处理。
> **格式:** YAML(同步脚本读)。这里给草案,实际进 `tools_dev/release/facade_whitelist.yaml`。

```yaml
# tools_dev/release/facade_whitelist.yaml (v0.1 草案)
license:
  default: MIT
  data_snapshot: CC-BY-NC-4.0

files:
  # 根目录
  - {src: README.md, sanitize: [strip_internal_links, replace_ip_to_domain]}
  - {src: LICENSE}
  - {src: CONTRIBUTING.md, sanitize: [strip_internal_links]}
  - {src: SECURITY.md}
  - {src: .gitignore, dest: .gitignore.facade}      # 重命名避免覆盖

  # 治理 / 标准(全部公开)
  - {src: docs/standards/AGENT_API_CONTRACT.md}
  - {src: docs/standards/AGENT_PROTOCOL_ROADMAP.md}
  - {src: docs/standards/DATA_GOVERNANCE_FRAMEWORK.md}
  - {src: docs/standards/DATA_CATALOG.md}
  - {src: docs/standards/DATA_LINEAGE.md}
  - {src: docs/standards/DATA_VERIFICATION_STANDARD.md}
  - {src: docs/standards/BRAND_INDEPENDENCE_AND_OSS_POLICY.md}
  - {src: docs/standards/MODEL_DATA_STANDARD.md}
  - {src: docs/standards/CATALOG_STANDARD.md}
  - {src: docs/standards/COLLISION_CLASSIFICATION_STANDARD.md}
  - {src: docs/standards/SYSTEM_DESIGN.md}
  - {src: docs/standards/PRICE_PAGE_STANDARD.md}
  - {src: docs/standards/PRICE_DATA_PIPELINE_STANDARD.md}
  - {src: docs/standards/PROVIDER_STATUS_STANDARD.md}
  - {src: docs/standards/DATA_QUALITY_AUDIT_STANDARD.md}
  - {src: docs/standards/EXPANSION_ROADMAP.md}
  - {src: docs/standards/FRAMEWORK_FINGERPRINT.md}
  - {src: docs/standards/RELEASE_STRATEGY.md}        # 本文档自身

  # OpenAPI 衍生品(发布时再生成)
  - {src: dist/openapi.v1.json, dest: openapi/v1.json, regenerate: web_openapi_export}

  # 治理脚本(无凭据,可公开)
  - {src: scripts/governance/build_data_catalog.py}

  # 测试样板(mocked, 不含真实 endpoint)
  - {src: tests/conftest.py}
  - {src: tests/detectors/test_token_billing.py, sanitize: [strip_internal_urls]}

  # CI
  - {src: .github/workflows/test.yml, sanitize: [strip_internal_secrets, set_python_matrix]}
  - {src: .github/ISSUE_TEMPLATE/}                   # 整目录

# 黑名单 patterns (regex,扫整库,命中即拒绝同步整个文件)
blacklist_patterns:
  - "192\\.168\\.\\d+\\.\\d+"            # 内网 IP
  - "10\\.\\d+\\.\\d+\\.\\d+"
  - "172\\.(1[6-9]|2\\d|3[0-1])\\.\\d+\\.\\d+"
  - "/home/debian/"                      # 本地绝对路径
  - "(?i)(sk-|api[_-]?key)[a-z0-9]{16,}" # 类 key 串
  - "(?i)tokenscanai\\.org"              # 旧域名(已迁 .com)
  - "canarybyte"                         # 旧 org
  - "(?i)(password|passwd|secret)\\s*[:=]\\s*['\"][^'\"]{4,}"

# 强制改写
rewrites:
  "192\\.168\\.1\\.102:6723": "https://tokenscanai.com"
  "tokenscanai\\.org": "tokenscanai.com"
  "/home/debian/tokenscan_v2/": "$REPO_ROOT/"
```

> §3 是**契约文档**,字段语义稳定;具体值会在 `facade_whitelist.yaml` 实施时小幅调整,但**新增/删除任何条目必须更新本文档**。

---

## 4. 同步脚本规格(`sync_to_facade.py`)

### 4.1 流程
```
[生产仓] --(读白名单)--> [scan + sanitize + rewrite] --(写 facade_workdir)
       --(diff against facade git)--> [人工 review (强制)]
       --(commit + 本机 git push 镜像到 facade local)
       --(再人工 git push origin main)  ← 最后一关人手
```

### 4.2 命令面板(待建)
```
python tools_dev/release/sync_to_facade.py scan     # 黑名单扫描,任何命中即非 0 退出
python tools_dev/release/sync_to_facade.py dry-run  # 输出 diff 但不写盘
python tools_dev/release/sync_to_facade.py build    # 写到 facade_workdir/
python tools_dev/release/sync_to_facade.py commit   # 本机 commit 到 ~/tokenscan_facade,不 push
```

> **禁止**:任何自动 `git push origin`,push 必须 TUI agent 手动跑,最后一关确保人在场。

### 4.3 强制 hook
- pre-build hook:跑 `scan`,黑名单 patterns 命中 → 非 0 退出 + 报错位置
- post-build hook:跑 `git diff --stat` 输出 review summary
- post-build hook 2:跑 `grep -rE "TODO|FIXME|XXX|HACK"` 报告(警告非阻塞)

---

## 5. 第一次发布前 checklist (一次性 hardening)

按顺序勾,**任何一项失败,首次发布推迟**。

| # | 项 | 验证命令 | 状态 |
|---|---|---|---|
| 1 | 生产仓 `git remote -v` 输出为空 | `cd /home/debian/tokenscan_v2 && git remote -v \| wc -l` 应为 0 | ✅ 已验 (2026-06-26) |
| 2 | LICENSE 是 MIT,无 AGPL 实质条款 | `head -1 LICENSE` = `MIT License` | ✅ 已验 (D6) |
| 3 | README 域名指向 `tokenscanai.com` / 仓库指向 `TokenScanAI/tokenapi-scan` | `grep -E "(tokenscanai\.org\|canarybyte)" README.md \| wc -l` 应为 0 | ✅ 已验 (D6) |
| 4 | 全仓黑名单扫描 0 命中 | `sync_to_facade.py scan` | ⏳ 脚本待建 |
| 5 | 门面仓 `TokenScanAI/tokenapi-scan` 当前内容已存档,准备清空重推 | gh CLI 备份当前 main → branch `legacy-pre-v0.1` | ⏳ 待执行 |
| 6 | CONTRIBUTING.md 提到的"开源仓库即将开放"改成实际链接 | 手改 | ⏳ |
| 7 | API 契约 v1 冻结(operation_id 已固化) | `curl /openapi.json` 22 端点全有 operation_id | ✅ 已验 (C2-day2) |
| 8 | SECURITY.md 含 vulnerabilities 上报路径 | `read SECURITY.md` | ⏳ 待确认 |
| 9 | CONTRIBUTING.md 清楚说明 issue/PR 渠道 | 手改 | ⏳ |
| 10 | `.gitignore.facade` 兜底:即使误推也屏蔽 `web_data/`,`.env*`,`*.db`,`*.bak.*`,`tools_dev/price_scraping/`,`src/relay_detector/protocols/` | 写入白名单时一并落 | ⏳ |

---

## 6. 持续发布流水线(首发后)

### 6.1 节奏
- **不做定时自动发布。** Layer 边界改动随时可能发生,人工 release 优于 cron。
- 每次发布触发器:开发者(我)主动跑同步脚本。
- 期望节奏:文档/治理 → 周级;API 契约 → 季级;SDK → 按需。

### 6.2 版本号
- **公开门面仓**走 SemVer:`v0.1.0` 起。
- v0.x:文档/契约期,API 可破坏变更
- v1.0.0:契约首次冻结,符合 `AGENT_API_CONTRACT.md` 兼容性矩阵
- patch:文档修正
- minor:新增 API / SDK
- major:契约破坏性变更(需 60 天 deprecate notice,见 API 契约文档)

### 6.3 Release artifact
- 门面仓 GitHub Release 附:
  - `openapi/v1.json` 当版本快照
  - `data-dictionary-v<x>.json`(由 `build_data_catalog.py` 导出公开版,去掉行数,只留 schema)
  - 不附 binary / db / data

### 6.4 Watchdog(L1 红线监控)
落 cron(本机,30 分钟一次):
```bash
# ~/.hermes/scripts/tokenapi_remote_guard.sh
cd /home/debian/tokenscan_v2
if [ -n "$(git remote -v)" ]; then
  echo "[CRITICAL] 生产仓 git remote 出现:$(git remote -v)" | wechat-notify
fi
```
绑入 `outbound_health_watchdog` 同一通知通道。

---

## 7. CI 策略(门面仓 only)

- 现有 `.github/workflows/test.yml` 跑 mocked detector tests,可保留
- **不引入**任何 self-hosted runner / 内网 secret
- **不引入**任何"对生产环境的真实探测"测试
- 增加 lint workflow:black + ruff + mypy(只对 SDK 部分)

---

## 8. 风险与回滚

| 风险 | 缓解 | 回滚 |
|---|---|---|
| 误把 Layer 3 文件推上去 | §5 checklist + §4 黑名单扫描 + 人工 review 三层 | gh release delete + git push --force-with-lease + 内容已被 mirror 的话申请 GitHub Support 抹除 |
| 门面仓 history 串入生产 commit | §2.1 选 B 物理隔离即解决 | n/a |
| LICENSE 选错(被外人合并 GPL 贡献) | CONTRIBUTING.md 必须含 DCO + CLA 简短声明:贡献即同意 MIT | 撤回 PR,联系贡献者改授权 |
| 数据快照含隐私 | 任何示例数据走 §3 黑名单扫描 + 人工抽审 | 重发新版本删除 |

---

## 9. 下一步(Sprint 1 子任务清单)

| # | 任务 | 工作量 | 优先级 |
|---|---|---|---|
| 1 | 写 `tools_dev/release/facade_whitelist.yaml`(§3 草案落地) | 0.5d | P0 |
| 2 | 写 `tools_dev/release/sync_to_facade.py`(§4 命令面板) | 1.5d | P0 |
| 3 | 备份 `TokenScanAI/tokenapi-scan` 当前 main → `legacy-pre-v0.1` branch (用 gh CLI,**只动门面仓不动生产**) | 0.5h | P0 |
| 4 | SECURITY.md / CONTRIBUTING.md 实际化 | 0.5h | P1 |
| 5 | 落 cron watchdog `tokenapi_remote_guard.sh` | 15min | P1 |
| 6 | Dry-run 一次 sync,人工 review 全输出 | 1h | P0 |
| 7 | 首次 release v0.1.0(等 §5 全过) | 1h | 走完 1-6 后 |

---

## 10. 变更记录

- **v0.1** (2026-06-26) — 初稿,选型 = 双仓物理隔离 + 单向同步,§3 白名单首版,§5 一次性 hardening checklist,§9 Sprint 1 子任务清单
