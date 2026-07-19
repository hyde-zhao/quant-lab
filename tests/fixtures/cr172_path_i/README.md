# CR-172 PATH-I S05 fixtures

本目录只承载 repository-local、test-only 的事实输入和预期 oracle：

- `scenario_catalog.json`：15 条 requirement、27 条 scenario、11 条 outcome 的精确映射。
- `sealed_chain_v1.json`：S02→S03→S04 确定性输入、固定时间和已封存 source-selection digest。
- `failure_mutations_v1.json`：tamper、partial-lineage、staging failure 与 previous-selection preservation 的预期结果。
- `zero_operation_oracle_v1.json`：六类真实动作、五项高阶 claim 和 deferred boundary 的零值 oracle。
- `path_i_fixture.py`：只组装上述事实并实现生产 port 抽象要求的纯内存 fixture；不实现真实 adapter。

生产规则的唯一真相源始终是 `engine/path_i_governance.py`、
`engine/trial_return_artifact.py`、`engine/research_artifact_replica.py` 和
`engine/research_artifact_materialization.py`。本目录不复制授权判定、canonical
serialization、digest、verifier、receipt、freshness、CAS 或 claim-ceiling 规则；测试只调用
这些模块的 public contract。静态 JSON 中的 digest 是固定输入/oracle，不是另一套计算器。

所有 URI 和 handle 都属于 `fixture://repository/**` 或仓库内相对句柄；本目录不读取 credential、
真实 lake/NAS/执行机，不发起网络、subprocess、mount、信号、交易、部署或 Git remote 操作。
