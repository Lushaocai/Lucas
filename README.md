<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/LushaocaiLushaocai/output/github-contribution-grid-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Lushaocai/Lushaocai/output/github-contribution-grid-snake.svg">
  <img alt="github contribution grid snake animation" src="https://raw.githubusercontent.com/Lushaocai/Lushaocai/output/github-contribution-grid-snake.svg">
</picture>

## G代码风格加料程序解析器

新增 `parser.py`，用于解析图片中定义的指令：

- `A01` 加配料（支持多组 `P|L + 料盒号 + A加料量`）
- `P01` 倒菜（`S|B`，可选震动时间）
- `C01` 开/关锅盖（`O|C`）
- `S01` 单段翻锅（方向+速度，动作次数或持续）
- `S02` 双段翻锅（两段方向+速度，动作次数或持续）
- `S03` 停止翻锅
- `T01` 设置锅温（`C温度`）
- `W01` 等待（可包含 `C温度` 与/或 `D延时`）

### 运行示例

```bash
python parser.py /absolute/path/to/program.txt
```

### 测试

```bash
python -m unittest discover -s tests
```
