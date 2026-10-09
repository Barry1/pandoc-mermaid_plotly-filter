#!/usr/bin/env python3
import json
import sys

from .core import render_to_file


def is_mermaid(block):
    if block.get("t") != "CodeBlock":
        return False
    try:
        attr, _ = block["c"]
        _, classes, _ = attr
        return "mermaid" in classes
    except:
        return False


def do_transform(block):
    attr, code = block["c"]
    _, _, kvs = attr
    kv = dict(kvs)
    w = int(kv.get("width", "1920"))
    h = int(kv.get("height", "1080"))
    title = kv.get("title", "")
    outdir = kv.get("outdir", None)
    out = render_to_file(code, w, h, title, outdir)
    # Pandoc Image: inlines, target
    img = {
        "t": "Image",
        "c": [["", [], []], [{"t": "Str", "c": title or "plotly"}], [str(out), ""]],
    }
    return {"t": "Para", "c": [img]}


def walk(o):
    if isinstance(o, dict):
        if o.get("t") == "CodeBlock" and is_mermaid(o):
            return do_transform(o)
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(x) for x in o]
    return o


def main():
    data = json.load(sys.stdin)
    data = walk(data)
    json.dump(data, sys.stdout)


if __name__ == "__main__":
    main()
