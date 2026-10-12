# 贡献指南 · TokenAPI Scan(照妖镜)

感谢你对 TokenAPI Scan 的关注。这是一个**MIT 许可**(自 2026-06-26 重新许可) + **三层分级开源**的项目:Layer 1 公开 / Layer 2 受控开源 / Layer 3 永久闭源,详见 `docs/standards/BRAND_INDEPENDENCE_AND_OSS_POLICY.md`。

## 1. 仓库说明

| 仓库 | 角色 | License |
|---|---|---|
| `TokenScanAI/tokenapi-scan` (GitHub) | **门面仓** — 文档 / API 契约 / SDK / Mock 测试 / CI | MIT |
| 内部生产仓 | 检测内核 / 生产数据 / 节点配置 | **不公开**(Layer 3) |

发布流程:生产仓**永远没有 git remote**(物理隔离),由 `tools_dev/release/sync_to_facade.py`(脚本完善中)走白名单 + 黑名单扫描,推到门面仓。详见 `docs/standards/RELEASE_STRATEGY.md`。

## 2. 接受什么贡献

### ✅ 欢迎

- **文档**:typo / 不准确 / 翻译 / 例子补充
- **数据字典 + 治理文档**:`docs/standards/*` 各 STANDARD/CATALOG/LINEAGE 文档的 PR
- **公开 SDK**:`sdk/evidence_store.py` 等 Layer 1 工具的 bug fix / 测试 / 示例
- **OpenAPI 契约**:`openapi/v1.json` 的兼容性反馈(发现 client 解析失败一定要报)
- **CI workflow** 改进:测试加快 / 矩阵覆盖更多 Python 版本
- **Issue / Discussion**:bug 报告 / 功能建议 / 数据质量反馈(模型字典纠错欢迎单开 issue)

### ⚠️ 不接受 / 不公开

- **检测内核 PR**(协议探测器、反爬绕过)——属于 Layer 3
- **真实端点列表 / 真实 API key 截图**——任何 PR 含此类直接 close,见 SECURITY.md §2.4
- **法律 / 商业模式 / 品牌策略相关讨论**——请走邮件 hi@tokenscanai.com

## 3. PR 流程

1. **先开 issue 讨论**(对非 typo / non-trivial 改动),避免做完工作发现方向不对
2. Fork → branch:`fix/<short-desc>` 或 `feat/<short-desc>`
3. 一个 PR 一件事;commits 用 [Conventional Commits](https://www.conventionalcommits.org/)(`fix:` `feat:` `docs:` `chore:`)
4. PR 描述含:
   - 改了什么 + 为什么(链接 issue)
   - 如何测试(给 reviewer 复现命令)
   - 是否破坏兼容(对 SDK / API)
5. CI 全绿(test workflow + lint)
6. 至少 1 名 maintainer review,涉及 SDK 公开接口的需 2 名

## 4. DCO + License 同意

提交 PR 即表示:

> "I agree to license my contribution under the **MIT License** of this repository.
> I have the right to submit this contribution(原创 / 已获授权)."

PR 模板里有勾选框;commits 建议带 `Signed-off-by: Your Name <email>`(git commit -s)。

我们**不要求 CLA**,但保留必要时切换到 CLA 的权利(会公开通告)。

## 5. 开发环境

```bash
git clone https://github.com/TokenScanAI/tokenapi-scan
cd tokenapi-scan
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/   # mocked tests, 不联网
```

代码风格:black + ruff + mypy(对 SDK 严格)。pre-commit hook 见 `.pre-commit-config.yaml`。

## 6. 数据 / 检测质量反馈

发现模型字典错误 / 价格不准 / 检测漏报误报:

- 开 issue 用 `data-quality` 模板
- 给现场:**具体 model_canonical_id + provider_id + 你看到的现象 + 期望值 + 来源 URL/截图**
- 我们 72h 内响应,合理反馈写入 `model_alias` 时会标注 confidence='community' + evidence_ref

## 7. 行为准则

- 尊重所有参与者,无骚扰 / 歧视 / 攻击
- 技术分歧用数据 + 复现命令解决,不用立场喊话
- 涉嫌恶意:close + ban,不解释
- 报告违反:hi@tokenscanai.com

## 8. 联系

- **issue / PR**:https://github.com/TokenScanAI/tokenapi-scan
- **安全**:security@tokenscanai.com(见 SECURITY.md)
- **一般咨询**:hi@tokenscanai.com
- **站点 / 微信群**:https://tokenscanai.com

---

最后更新:2026-06-27 · v2(对齐 RELEASE_STRATEGY v0.1)
