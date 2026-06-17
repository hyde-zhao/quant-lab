# MiniQMT Runner Target

本 target 描述未来在 MiniQMT runner 环境中消费 `qmt_interface_smoke` 的边界。当前文件只作为离线策略包材料，不包含 runner 安装器或连接脚本。

## 可验证内容

- package manifest 中存在 `miniqmt_runner` target。
- `runtime_authorized=false`，说明当前包不能触发 MiniQMT / XtQuant / gateway 运行。
- 本 target 只能参与离线 package intake、manifest 校验和证据模板检查。

## 不允许的影响

- 不修改交易主机环境变量、系统服务、启动项或依赖安装。
- 不启动 MiniQMT、gateway、HTTP 服务或 socket。
- 不读取凭据，不查询账户原文，不提交或撤销任何委托。
- 不把 NAS 目录作为默认执行根。

## 后续授权后的消费方式

若后续单独授权 runtime smoke，MiniQMT runner 应从交易主机本地不可变缓存读取包，而不是从 NAS 原地执行。缓存入口由 `manifest.yaml` 的 `trading_host_contract` 描述，active pointer 只能在 package 校验通过后由人工或已授权流程切换。
