"""v11 Lua 클립 입출력.

클립 파일 형식 (v10 과 동일):
    -- 주석 줄 (0개 이상)
    return {
    	duration = 1,
    	... 스칼라 필드 (full, loop, hitAt, cut, jumpAt, posScale ...)
    	parts = { "MAC_R_UpperArm", ... },
    	frames = {
    {t, 파트0 pos xyz, quat wxyz, 파트1 ..., ...},
    	},
    }
행 = t + 파트 9개 × 7값. pos 는 휴지 대비 이동량(m, 게임에서 posScale 곱), quat 는 휴지 대비 회전.
Blender 없이 순수 파이썬으로 동작한다 (bl_execute 안에서도 import 가능).
"""
import os
import re

PARTS = [
    "MAC_R_UpperArm", "MAC_R_LowerArm", "MAC_R_Hand",
    "MAC_L_UpperArm", "MAC_L_LowerArm", "MAC_L_Hand",
    "MAC_Handle", "MAC_Body", "MAC_Obsidian",
]
VALUES_PER_PART = 7


def fmt(v):
    """v10 숫자 표기: 소수 4자리, 앞 0 생략, 뒤 0 생략."""
    s = "%.4f" % v
    s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def _scalar(text):
    text = text.strip()
    if text == "true":
        return True
    if text == "false":
        return False
    return float(text)


def read_clip(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines()
    comments = [l for l in lines if l.startswith("--")]
    head, _, body = src.partition("frames = {")
    fields = []
    for m in re.finditer(r"^\t(\w+) = ([^{\n]+?),\s*$", head, re.M):
        fields.append((m.group(1), _scalar(m.group(2))))
    parts = re.findall(r'"([^"]+)"', head.partition("parts = {")[2])
    frames = []
    for m in re.finditer(r"^\{([^}]*)\},?\s*$", body, re.M):
        frames.append([float(x) for x in m.group(1).split(",")])
    n = 1 + len(parts) * VALUES_PER_PART
    bad = [i for i, r in enumerate(frames) if len(r) != n]
    if bad:
        raise ValueError("%s: 열 수가 %d 가 아닌 행 %s" % (path, n, bad[:5]))
    return {"comments": comments, "fields": fields, "parts": parts, "frames": frames}


def field(clip, key, default=None):
    for k, v in clip["fields"]:
        if k == key:
            return v
    return default


def set_field(clip, key, value):
    for i, (k, _) in enumerate(clip["fields"]):
        if k == key:
            clip["fields"][i] = (key, value)
            return
    clip["fields"].append((key, value))


def part_track(clip, part):
    """프레임별 (pos(3), quat wxyz(4)) 목록."""
    i = clip["parts"].index(part)
    o = 1 + i * VALUES_PER_PART
    return [(r[o:o + 3], r[o + 3:o + 7]) for r in clip["frames"]]


def write_clip(path, clip):
    out = list(clip["comments"])
    out.append("return {")
    for k, v in clip["fields"]:
        if isinstance(v, bool):
            s = "true" if v else "false"
        else:
            s = fmt(v)
        out.append("\t%s = %s," % (k, s))
    names = ['"%s"' % p for p in clip["parts"]]
    out.append("\tparts = {")
    for i in range(0, len(names), 6):
        out.append("\t\t" + ", ".join(names[i:i + 6]) + ",")
    out.append("\t},")
    out.append("\tframes = {")
    for r in clip["frames"]:
        out.append("{" + ",".join(fmt(x) for x in r) + "},")
    out.append("\t},")
    out.append("}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def roundtrip_check(folder):
    """폴더의 모든 클립을 읽고 다시 써서 원문과 비교한다. 반환: {파일: 결과}."""
    import tempfile
    report = {}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".lua"):
            continue
        p = os.path.join(folder, name)
        clip = read_clip(p)
        tmp = os.path.join(tempfile.gettempdir(), "v11_rt_" + name)
        write_clip(tmp, clip)
        same = open(p, encoding="utf-8").read() == open(tmp, encoding="utf-8").read()
        back = read_clip(tmp)
        err = max(abs(a - b) for ra, rb in zip(clip["frames"], back["frames"]) for a, b in zip(ra, rb))
        report[name] = {"rows": len(clip["frames"]), "text_identical": same, "max_value_err": err,
                        "fields": [k for k, _ in clip["fields"]]}
        os.remove(tmp)
    return report


if __name__ == "__main__":
    import json
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("Clips", "Transitions"):
        r = roundtrip_check(os.path.join(root, sub))
        print(sub, "files", len(r), "text_identical", sum(v["text_identical"] for v in r.values()),
              "max_err", max(v["max_value_err"] for v in r.values()))
        for k, v in r.items():
            if not v["text_identical"]:
                print("  DIFF", k, v)
