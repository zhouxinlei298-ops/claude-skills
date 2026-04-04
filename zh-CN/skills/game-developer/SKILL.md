---
name: game-developer
description: "Use when building game systems, implementing Unity/Unreal Engine features, or optimizing game performance. Invoke to implement ECS architecture, configure physics systems and colliders, set up multiplayer networking with lag compensation, optimize frame rates to 60+ FPS targets, develop shaders, or apply game design patterns such as object pooling and state machines. Trigger keywords: Unity, Unreal Engine, game development, ECS architecture, game physics, multiplayer networking, game optimization, shader programming, game AI."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: specialized
  triggers: Unity, Unreal Engine, game development, ECS architecture, game physics, multiplayer networking, game optimization, shader programming, game AI
  role: specialist
  scope: implementation
  output-format: code
  related-skills:
---

# Game Developer

## 核心工作流程

1. **分析需求** — 确定游戏类型、目标平台、性能目标、多人游戏需求
2. **设计架构** — 规划 ECS/组件系统，针对目标平台进行优化
3. **实现** — 构建核心机制、图形、物理、AI、网络
4. **优化** — 性能分析和优化以实现 60+ FPS，最小化内存/电池消耗
   - **验证检查点：** 运行 Unity Profiler 或 Unreal Insights；确认帧时间 ≤16 毫秒（60 FPS）后再继续。迭代识别并解决 CPU/GPU 瓶颈。
5. **测试** — 跨平台测试、性能验证、多人压力测试
   - **验证检查点：** 确认在压力负载下帧率稳定；在发布前运行多人延迟/不同步测试。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| Unity 开发 | `references/unity-patterns.md` | Unity C#、MonoBehaviour、Scriptable Objects |
| Unreal 开发 | `references/unreal-cpp.md` | Unreal C++、Blueprints、Actor 组件 |
| ECS 与模式 | `references/ecs-patterns.md` | 实体组件系统、游戏设计模式 |
| 性能 | `references/performance-optimization.md` | FPS 优化、性能分析、内存 |
| 网络 | `references/multiplayer-networking.md` | 多人游戏、客户端-服务器、延迟补偿 |

## 约束

### 必须做
- 所有平台目标 60+ FPS
- 对频繁实例化使用对象池
- 实现 LOD 系统进行优化
- 定期进行性能分析（CPU、GPU、内存）
- 使用异步加载资源
- 为游戏逻辑实现正确的状态机
- 缓存组件引用（避免在 Update 中调用 GetComponent）
- 使用 delta time 实现帧率无关移动

### 不能做
- 在紧密循环或 Update() 中实例化/销毁
- 跳过性能分析和性能测试
- 使用字符串比较标签（使用 CompareTag）
- 在 Update/FixedUpdate 循环中分配内存
- 忽略平台特定约束（移动端、主机）
- 在 Update 循环中使用 Find 方法
- 硬编码游戏数值（使用 ScriptableObjects/数据文件）

## 输出模板

实现游戏功能时，请提供：
1. 核心系统实现（ECS 组件、MonoBehaviour 或 Actor）
2. 相关数据结构（ScriptableObjects、结构体、配置）
3. 性能考虑和优化
4. 架构决策的简要说明

## 关键代码模式

### 对象池（Unity C#）
```csharp
public class ObjectPool<T> where T : Component
{
    private readonly Queue<T> _pool = new();
    private readonly T _prefab;
    private readonly Transform _parent;

    public ObjectPool(T prefab, int initialSize, Transform parent = null)
    {
        _prefab = prefab;
        _parent = parent;
        for (int i = 0; i < initialSize; i++)
            Release(Create());
    }

    public T Get()
    {
        T obj = _pool.Count > 0 ? _pool.Dequeue() : Create();
        obj.gameObject.SetActive(true);
        return obj;
    }

    public void Release(T obj)
    {
        obj.gameObject.SetActive(false);
        _pool.Enqueue(obj);
    }

    private T Create() => Object.Instantiate(_prefab, _parent);
}
```

### 组件缓存（Unity C#）
```csharp
public class PlayerController : MonoBehaviour
{
    // 在 Awake 中缓存所有组件引用 — 永远不要在 Update 中调用 GetComponent
    private Rigidbody _rb;
    private Animator _animator;
    private PlayerInput _input;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody>();
        _animator = GetComponent<Animator>();
        _input = GetComponent<PlayerInput>();
    }

    private void FixedUpdate()
    {
        // 使用缓存的引用；使用 deltaTime 实现帧率无关
        Vector3 move = _input.MoveDirection * (speed * Time.fixedDeltaTime);
        _rb.MovePosition(_rb.position + move);
    }
}
```

### 状态机（Unity C#）
```csharp
public abstract class State
{
    public abstract void Enter();
    public abstract void Tick(float deltaTime);
    public abstract void Exit();
}

public class StateMachine
{
    private State _current;

    public void TransitionTo(State next)
    {
        _current?.Exit();
        _current = next;
        _current.Enter();
    }

    public void Tick(float deltaTime) => _current?.Tick(deltaTime);
}

// 使用示例
public class IdleState : State
{
    private readonly Animator _animator;
    public IdleState(Animator animator) => _animator = animator;
    public override void Enter() => _animator.SetTrigger("Idle");
    public override void Tick(float deltaTime) { /* 轮询状态转换 */ }
    public override void Exit() { }
}
```
