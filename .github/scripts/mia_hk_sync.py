#!/usr/bin/env python3
"""拉 bestcf 的 Mia 节点，只取 HK，替换 youxuanip.txt 里的 #Mia-HK- 行，其余一律不动"""
import re, sys, urllib.request, pathlib

SRC    = "https://bestcf.pages.dev/xinyitang3/ipv4.txt"
TARGET = pathlib.Path("youxuanip.txt")
ZW     = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)  # 节点名里全是零宽字符
MIA    = re.compile(r"^.+:\d+#Mia-HK-")                             # 现有文件里的锚点
# 源里的名字长这样：Mia优选 | HK TG:@MiaChatChannel | 27.44.142.135:10001
HK     = re.compile(r"\bHK\b")

# 1) 拉源，取 HK
req  = urllib.request.Request(SRC, headers={"User-Agent": "curl/8"})
text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

seen, hk = set(), []
for line in text.splitlines():
    line = line.translate(ZW).strip()          # 零宽清掉再判，否则 HK 永远匹配不到
    m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d+)#(.+)$", line)
    if not m or not HK.search(m.group(3)):
        continue
    key = f"{m.group(1)}:{m.group(2)}"
    if key not in seen:
        seen.add(key)
        hk.append(key)

if not hk:
    sys.exit("源里没有 HK 节点，仓库保持不动")

new_rows = [f"{k}#Mia-HK-{i:02d}" for i, k in enumerate(hk, 1)]

# 2) 找锚点
old_lines = TARGET.read_text(encoding="utf-8").splitlines()
idx = next((i for i, l in enumerate(old_lines) if MIA.match(l)), None)
if idx is None:
    sys.exit("现有文件里找不到 #Mia-HK- 行，不知道插哪，中止")

kept      = [l for l in old_lines if not MIA.match(l)]
new_lines = kept[:idx] + new_rows + kept[idx:]

# 3) 保险：非 Mia 行必须逐字节不变（东京 10 行、#HK-0X/#HK-0Y、空行）
if [l for l in new_lines if not MIA.match(l)] != kept:
    sys.exit("非 Mia 行被改动，中止")
tok_old = [l for l in old_lines if "#CF东京-" in l]
tok_new = [l for l in new_lines if "#CF东京-" in l]
if len(tok_old) != 10 or tok_old != tok_new:
    sys.exit(f"东京行异常（旧 {len(tok_old)} / 新 {len(tok_new)}），中止")

# 4) 写回
TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"替换 {sum(1 for l in old_lines if MIA.match(l))} 行 -> {len(new_rows)} 行")
print("\n".join(new_rows))
