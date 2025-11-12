BLOCK = ["rope", "kys", "kill yourself"]  # filtered; toned-down alternatives used

def sanitize(text: str) -> str:
    t = text
    for b in BLOCK:
        t = t.replace(b, "***")
    return t
