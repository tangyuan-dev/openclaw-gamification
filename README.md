# 🎮 OpenClaw 游戏化学习系统 V2

自动化追踪 · 自动生成 · 智能推送

## 🎯 核心理念

**自动** > 手动

- ✅ 自动追踪 GitHub 学习数据
- ✅ 达成成就自动生成卡片
- ✅ 自动推送到学员的渠道

---

## 🔄 自动追踪流程

```
GitHub活动 → 自动记录 → 积分计算 → 成就检测 → 自动推送卡片
```

### 自动追踪的数据

| 数据源 | 追踪内容 |
|--------|---------|
| GitHub Commits | 提交代码 +20分 |
| GitHub Issues | 打卡 +5分 |
| GitHub PR | 贡献教程 +50分 |
| GitHub Stars | 获得关注 +1分 |

---

## 🎖️ 成就自动触发

| 成就 | 条件 | 自动触发 |
|------|------|---------|
| 🌱 新手 | 注册 | 自动推送欢迎卡 |
| 📖 学徒 | 100分 | 自动推送成就卡 |
| 💻 开发者 | 200分 | 自动推送成就卡 |
| 🔥 坚持者 | 7天连续 | 自动推送成就卡 |
| 🎓 导师 | 500分 | 自动推送成就卡 |
| 🏆 大师 | 1000分 | 自动推送成就卡 |

---

## 📤 自动推送渠道

### 支持的渠道

- 📱 Telegram
- 💬 Discord  
- �飞书
- 📧 Email
- 🐦 Twitter

### 推送示例

```
🎉 恭喜！解锁新成就！

🏅 成就：💻 开发者
📊 当前积分：200
🎖️ 成就进度：5/9

[查看你的成就卡片]
```

---

## 🛠️ 技术实现

### 1. GitHub Webhook 自动记录

```yaml
# .github/workflows/tracker.yml
name: 学习追踪

on:
  push:
    branches: [main, master]
  issues:
    types: [opened]
  pull_request:
    types: [opened, merged]

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - name: 记录学习活动
        run: |
          # 记录积分
          echo "记录 activity..."
          
          # 更新数据库
          curl -X POST ${{ secrets.API_URL }}/track \
            -d "user=${{ github.actor }}&action=${{ github.event_name }}&points=${{ env.POINTS }}"
```

### 2. 自动检测成就

```python
# auto_badge.py
def check_achievements(user_id):
    user_data = get_user_data(user_id)
    new_badges = []
    
    # 检查每个成就
    for badge in BADGE_DEFINITIONS:
        if badge not in user_data.badges:
            if badge.condition(user_data.points):
                new_badges.append(badge)
                user_data.badges.append(badge)
                
                # 自动生成并推送卡片
                generate_and_push_card(user_data, badge)
    
    save_user_data(user_data)
    return new_badges
```

### 3. 自动生成卡片

```python
def generate_card(user_data, badge):
    # 生成图片
    img = create_achievement_card(
        username=user_data.username,
        points=user_data.points,
        badge=badge,
        streak=user_data.streak,
        level=user_data.level
    )
    
    # 推送到用户渠道
    push_to_user(user_data, img)
```

---

## 📊 成就卡片示例

### 自动生成的卡片内容

```
┌─────────────────────────────┐
│  🎉 新成就解锁！              │
│                             │
│  🏅 开发者                   │
│  ─────────────────────      │
│  👤 tangyuan-dev           │
│  💰 200 积分                │
│  🔥 7 天连续打卡             │
│  ─────────────────────      │
│  📊 5/9 成就                 │
│                             │
│  🎮 OpenClaw 游戏化学习     │
└─────────────────────────────┘
```

---

## 🚀 快速接入

### 学员端

```bash
# 1. Fork 学习仓库
git clone https://github.com/tangyuan-dev/openclaw-tutorials.git

# 2. 开始学习
# 自动追踪开始！

# 3. 获得成就
# 自动收到推送
```

### 管理员端

```bash
# 部署追踪服务
docker run -d -p 3000:3000 \
  -e GITHUB_TOKEN=$TOKEN \
  -e DATABASE_URL=$URL \
  openclaw-gamification-server
```

---

## 📦 相关仓库

- [openclaw-gamification](https://github.com/tangyuan-dev/openclaw-gamification) — 游戏化系统
- [openclaw-gamification-tools](https://github.com/tangyuan-dev/openclaw-gamification-tools) — 工具集
- [openclaw-gamification-server](https://github.com/tangyuan-dev/openclaw-gamification-server) — 自动追踪服务（开发中）

---

## 🎮 立即加入

1. ⭐ Star 本系统
2. 📚 开始学习教程
3. 🎉 自动获得成就

---

<div align="center">

**让学习像玩游戏一样有趣！**

</div>
