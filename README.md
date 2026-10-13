# 虚空到恒星

一款宇宙题材的像素风增量游戏：从虚空中聚集第一粒尘埃，长成行星、褐矮星，最终点燃恒星并坍缩，开启下一个宇宙。

## 在线游玩

| 版本 | 链接 | 内容 |
| --- | --- | --- |
| 最新版 | https://littlewhite1024.github.io/void-to-star/ | 始终是最新发布的版本 |
| v0.1.1 | https://littlewhite1024.github.io/void-to-star/v0.1.1/ | 修复：最小化或切换标签页后游戏暂停。回来时自动补算离开期间的进度（恒星阶段补算时铁最多到 98%，坍缩留到玩家回来） |
| v0.1 | https://littlewhite1024.github.io/void-to-star/v0.1/ | 虚空 → 恒星 7 个阶段、吸积源、三路线进化树与隐藏终局、恒星坍缩重置、宇宙常数、音效与背景音乐 |

每个版本都是一个独立的 `index.html`，背景音乐已内嵌，存档保存在浏览器本地。

## 目录结构

```
index.html          最新版入口（由 tools/build.py 生成，不要手改）
v0.1/index.html     v0.1 的冻结副本（发布后不再改动）
src/                源码：游戏页面和背景音乐
tools/build.py      把 src/ 打包成单文件版本
tools/bgm.py        背景音乐合成脚本（Python + numpy + scipy）
docs/               策划相关文件（进化树数值表）
```

## 发布新版本

1. 修改 `src/void-to-star.html`
2. 运行 `python tools/build.py 0.2`，生成 `v0.2/index.html` 并更新根目录的 `index.html`
3. 在上面的版本表里加一行
4. 提交后打标签：`git tag -a v0.2 -m "v0.2"`，再 `git push origin main --tags`

旧版本的文件夹保持不动，所以每个历史版本都能一直通过自己的链接游玩。

## 版本与源码

- **玩某个版本**：打开上表里对应的链接。
- **看某个版本的源码**：每个版本都有 git 标签，`git checkout v0.1` 即可切换到当时的完整项目。

## 注意：存档

所有版本放在同一个网址下，浏览器存档是共享存储。v0.1 的存档键名是 `void-to-star-v01`，以后的版本如果改动了存档结构，要换一个新的键名（或写迁移代码），避免新旧版本互相读坏存档。
