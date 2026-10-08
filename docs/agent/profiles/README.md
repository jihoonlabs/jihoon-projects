# Agent Profiles

Agentは万能化せず、作業に必要なProfileだけ切り替えて使う。

最初の実験Profile:
- `continuation`: 既存作業を 이어서 구현・검증・통합
- `zero-base`: 기존 결론을 전제하지 않는 독립 재검토

作業MDで例:
```
agent_profile: continuation
```

または:
```
agent_profile: zero-base
```

Profileは小さく保つ。
実作業で明確な必要が出るまで新Profileを増やさない。
