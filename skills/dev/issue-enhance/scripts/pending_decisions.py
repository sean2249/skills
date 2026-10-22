#!/usr/bin/env python3
"""Read the author's answers to the `## Pending decisions` section of an issue body.

Usage:
  gh issue view <N> --json body --jq .body | python3 pending_decisions.py
  python3 pending_decisions.py --comment "1: A, 2: other — use the cache"   # answers given in a comment

Prints JSON: one entry per decision with its status:
  answered      exactly one box ticked (for Other, the "Other:" line is filled in)
  unanswered    no box ticked
  multiple      more than one box ticked
  other-empty   Other ticked but the "Other:" line is empty
Exit code is 0 either way; read "all_answered" in the output.
"""
import json
import re
import sys

SECTION = re.compile(r"^##\s+Pending decisions\s*$", re.M)
NEXT_H2 = re.compile(r"^##\s+\S", re.M)
DECISION = re.compile(r"^###\s+(?:Decision|決策)\s*(\d+)\s*[:：]\s*(.*)$", re.M)
BOX = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(A|B|C|D|Other|其他)(?=$|[\s:：(（])\s*[:：]?\s*(.*)$")
OTHER_LINE = re.compile(r"^\s*(?:Other|其他)\s*[:：]\s*(.*)$")


def section(body):
    m = SECTION.search(body)
    if not m:
        return None
    rest = body[m.end():]
    n = NEXT_H2.search(rest)
    return rest[: n.start()] if n else rest


def parse(body):
    sec = section(body)
    if sec is None:
        return None
    heads = list(DECISION.finditer(sec))
    out = []
    for i, h in enumerate(heads):
        block = sec[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(sec)]
        boxes, other_text = [], ""
        for line in block.splitlines():
            b = BOX.match(line)
            if b:
                key = "Other" if b.group(2) in ("Other", "其他") else b.group(2)
                boxes.append({"key": key, "text": (b.group(3) or "").strip(), "checked": b.group(1) != " "})
                continue
            o = OTHER_LINE.match(line)
            if o:
                other_text = o.group(1).strip()
        checked = [b for b in boxes if b["checked"]]
        if not checked:
            status, answer = "unanswered", None
        elif len(checked) > 1:
            status, answer = "multiple", None
        elif checked[0]["key"] == "Other" and not other_text:
            status, answer = "other-empty", None
        else:
            c = checked[0]
            status = "answered"
            answer = {"choice": c["key"], "text": other_text if c["key"] == "Other" else c["text"]}
        out.append({"n": int(h.group(1)), "title": h.group(2).strip(), "status": status,
                    "answer": answer, "any_checked": bool(checked)})
    return out


def parse_comment(text):
    """Answers like '1: A, 2: B' or '1：其他 用快取' in a comment."""
    out = {}
    for m in re.finditer(r"(\d+)\s*[:：]\s*(A|B|C|D|Other|other|其他)(?=$|[\s,，;；:：(（])\s*((?:(?!\d+\s*[:：])[^\n,，;；])*)", text):
        key = "Other" if m.group(2).lower() == "other" or m.group(2) == "其他" else m.group(2)
        out[int(m.group(1))] = {"choice": key, "text": m.group(3).strip(" —-")}
    return out


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--comment":
        print(json.dumps(parse_comment(sys.argv[2]), ensure_ascii=False, indent=2))
        return
    body = sys.stdin.read()
    decisions = parse(body)
    if decisions is None:
        print(json.dumps({"section": False}, ensure_ascii=False))
        return
    print(json.dumps({"section": True, "decisions": decisions,
                      "all_answered": bool(decisions) and all(d["status"] == "answered" for d in decisions),
                      "all_ticked": bool(decisions) and all(d["any_checked"] for d in decisions)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
