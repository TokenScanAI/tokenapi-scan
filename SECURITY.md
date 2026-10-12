# 安全策略 · TokenAPI Scan(照妖镜)

## 1. 项目背景

TokenAPI Scan 是一个**独立维护**的 AI API 中转站真伪与质量检测平台,域名 [tokenscanai.com](https://tokenscanai.com),代码仓库 `TokenScanAI/tokenapi-scan`(门面仓,详见 `docs/standards/RELEASE_STRATEGY.md`)。

本项目沿用 MIT License(自 2026-06-26 起,从原 AGPL-3.0 重新许可)。Layer 1 公开材料(API 契约 / SDK / 治理文档)走 MIT,Layer 3 检测内核与生产数据**永久闭源**,详见 `docs/standards/BRAND_INDEPENDENCE_AND_OSS_POLICY.md`。

## 2. 报告安全漏洞

如果你在 TokenAPI Scan 中发现安全问题,请优先通过**私密渠道**反馈,不要在公开 issue 或论坛披露。

### 2.1 推荐渠道

- **GitHub Security Advisory**(优先):https://github.com/TokenScanAI/tokenapi-scan/security/advisories/new
- **邮箱**:security@tokenscanai.com(PGP key 见站点 `/security/pgp.asc`,待发布)
- **微信**:站点底部社区入口,@项目负责人

### 2.2 报告应包含

- 漏洞类型(注入 / XSS / RCE / 凭据泄露 / 权限绕过等)
- 复现步骤(尽可能给最小可重现示例)
- 受影响的版本 / 部署形态(站点 / SDK / 检测脚本)
- PoC(如可) + 攻击场景描述
- 你希望被致谢的署名(可匿名)

### 2.3 响应承诺

| 阶段 | SLA | 反馈 |
|---|---|---|
| 收到 | 24 小时内 | 确认收到 + 内部追踪号 |
| 初步评估 | 72 小时内 | 危险等级 + 修复路线 |
| 修复 | 高危 14 天 / 中危 30 天 / 低危 90 天 | 私密验证版本 |
| 公开披露 | 修复推送后 + 你同意 | 致谢列表 + CVE(如适用) |

### 2.4 安全边界

**受范围保护**:
- 站点 `tokenscanai.com` + `api.tokenscanai.com`
- 公开 SDK(`clients/python`, `clients/mcp`)
- 公开规范文档中的协议契约部分

**不受范围保护**(请勿测试):
- 第三方中转站(我们检测的对象);若发现它们漏洞请联系对方
- 我们的检测节点 IP / 代理出口(Layer 3 闭源,故意不公开)
- 任何 `web_data/` 路径(生产数据,non-public)

## 3. 用户端安全最佳实践

### 3.1 API Key 处理

TokenAPI Scan 检测站点**不长期落盘**用户 API key:
- 站点检测器执行期间,key 在内存 ≤ 单次请求生命周期
- 探测请求结束立即丢弃,raw response 落盘前打码((mask `sk-xxx****yyyy`)
- 落盘 evidence 经 `src/governance/evidence_store.py`,可审计 + 可删除

但 **API key 安全主要在你这边**:
- 检测前先轮换出一个**临时受限 key**,检测完作废
- 不要把生产 key 直接喂检测站
- 关注 key 的请求/限额异常

### 3.2 中转站选择

检测通过 ≠ 100% 安全。建议:
- 优先有公开运营主体 + ICP 备案 + HTTPS 完整证书链的站点
- 看 TokenAPI Scan 的"协议覆盖 + 一致性 + 价格"三维评分,不只看单维指标
- 不要在不可信中转站使用高权限 key(全模型 + 无 RPM 限制)

### 3.3 数据共享

- 我们公开的数据(模型字典 / 价格快照)走 CC-BY-NC 4.0,可引用 + 注明来源
- 检测样本默认脱敏;你提交的 raw response 仅用于改进检测,**不外传第三方**

## 4. 运营者侧安全(私有部署)

如果你本地部署 TokenAPI Scan 检测内核(Layer 3 闭源,但 SDK + 治理文档公开):
1. **不开公网**——检测节点 IP 一旦泄露会被反爬封禁,看 `tokenapi-price-scraping` skill
2. 定期更新依赖:`pip install -U -r requirements.txt`
3. 数据库走 WAL + 加密快照,**禁止把生产 DB 推 git**(见 `RELEASE_STRATEGY.md` §2.2)
4. 监控:`tokenapi_remote_guard.sh`(cron 30 分钟) + `outbound_health_watchdog`

## 5. 致谢

感谢所有为 TokenAPI Scan 安全做出贡献的研究者。Hall of Fame 见 https://tokenscanai.com/security/hall-of-fame(待启用)。

---

最后更新:2026-06-27
策略版本:v2(对齐 RELEASE_STRATEGY v0.1)
