def unique_by_id(items):
    seen = {}
    for item in items:
        seen[item.id] = item
    return list(seen.values())