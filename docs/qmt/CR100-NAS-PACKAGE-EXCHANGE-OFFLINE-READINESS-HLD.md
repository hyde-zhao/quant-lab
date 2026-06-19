# CR100 NAS Package Exchange Offline Readiness HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v1.0 | 2026-06-19 | host-orchestrator | 初版，定义离线 fake exchange readiness 与真实 NAS 后置门禁。 |

## 1. 问题定义

CR091 已完成离线 runner 与本地 package/cache intake，但真实策略包从 research_pc 经 NAS exchange 到 trading_pc local immutable cache 的交付链尚未形成可验证合同。当前 NAS 不可连接，且用户未授权任何 NAS 访问，因此 CR100 只能交付 offline readiness。

成功标准：

- 本地 fake exchange root 必须通过 marker 防误用，缺 marker 时 100% fail closed。
- package manifest 至少覆盖 6 类字段：identity、target platforms、entrypoints、approval、hashes、permissions。
- 聚焦测试覆盖至少 7 个用例，包含成功路径和 4 类失败路径。
- forbidden operation counters 全部为 0。
- 真实 NAS publish / pull / copy / 校验操作执行次数为 0。

## 2. 推荐架构

```text
research_pc/local dev
  package root
    manifest.yaml
    strategy_core/
    targets/
    validation/
    docs/
      |
      | fake-publish, local only
      v
local fake exchange root
  .cr100_fake_exchange_root
  index.yaml
  packages/<package_id>/<version>/
      |
      | fake-pull, local only
      v
local cache root
  immutable/<package_id>-<version>/
  active.json
```

真实 NAS 恢复后，上图中的 `local fake exchange root` 才能在独立授权 gate 中替换为真实 exchange root。本轮不会替换。

## 3. 模块职责

| 模块 | 职责 | 禁止行为 |
|---|---|---|
| `trading.strategy_runner.package_exchange` | manifest 校验、fake root marker 校验、fake publish / pull / exchange check | NAS 访问、环境变量读取、runtime 启动、交易动作 |
| `scripts/cr100_package_exchange.py` | CLI 包装 init/check/publish/pull/check | 网络、QMT、dotenv、subprocess |
| `tests/test_cr100_package_exchange.py` | 本地 fixture 验证和负向用例 | 真实 NAS、真实凭据、真实 runtime |
| `CR100 recovery runbook` | NAS 恢复后人工验证步骤 | 保存真实路径、凭据或账户原文 |

## 4. Manifest 合同

最小字段：

```yaml
schema_version: cr100-strategy-package-manifest-v1
package_id: qmt_interface_smoke
package_version: 0.1.0
created_at: "2026-06-19T00:00:00+08:00"
target_platforms: [qmt_terminal, miniqmt_runner]
entrypoints:
  qmt_terminal: targets/qmt_terminal/entry.py
  miniqmt_runner: targets/miniqmt_runner/entry.py
approval:
  status: approved
hashes:
  strategy_core/strategy.py: sha256:<digest>
permissions:
  runtime: false
  submit_cancel: false
  simulation_live: false
  credential_read: false
  nas_read: false
  nas_write: false
```

## 5. Fail Closed 规则

| 条件 | 行为 |
|---|---|
| exchange root 缺 `.cr100_fake_exchange_root` | fail closed |
| manifest 缺失或 schema 不匹配 | fail closed |
| approval 不是 `approved` | fail closed |
| permissions 任一授权 flag 非 false | fail closed |
| entrypoint 越界、缺失或绝对路径 | fail closed |
| hash 缺失、格式错误或 mismatch | fail closed |
| package 内存在 symlink、`.env` 或 secret / token / credential / account 文件名 | fail closed |
| cache target 已存在 | fail closed，不覆盖 immutable package |

## 6. 安全与权限

CR100 的 approve 只代表同意本地离线 readiness。它不授权真实 NAS、凭据、账户、runtime、交易或 publish。CLI 输出包含 `not_authorization=true` 和 `real_nas_operations=false`，并固定 forbidden operation counters 为 0。

## 7. Gotchas

- fake exchange 不是 NAS 模拟器；它只证明合同、目录结构和错误路径，不证明挂载、权限、Windows 路径或 SMB/NFS 行为。
- `approved` 只表示离线 manifest 状态，不表示用户授权真实 publish。
- active pointer 只在本地 cache 中更新；真实 trading_pc active switch 必须未来单独授权。
- 不要把 CR089 的 blocked-readiness-approved 解读为 CR100 已恢复 CR089。
