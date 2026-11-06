"""Validate labeled image datasets against exact duplicates and split leakage."""
import hashlib
import json

def digest(image):
    if not image or not image[0] or any(len(row) != len(image[0]) for row in image):
        raise ValueError("Rectangular nonempty image required")
    if any(type(pixel) is not int or pixel < 0 or pixel > 255 for row in image for pixel in row):
        raise ValueError("8-bit grayscale pixels required")
    return hashlib.sha256(json.dumps(image, separators=(",", ":")).encode()).hexdigest()

def audit(train, test):
    seen_ids, by_digest = set(), {}
    collisions = []
    for split, rows in (("train", train), ("test", test)):
        for row in rows:
            identifier = row["id"]
            if not isinstance(identifier, str) or not identifier or identifier in seen_ids:
                raise ValueError("Missing or duplicate image id")
            if type(row["defective"]) is not bool:
                raise ValueError("Ground-truth label must be boolean")
            seen_ids.add(identifier)
            fingerprint = digest(row["image"])
            if fingerprint in by_digest:
                collisions.append({"first_id": by_digest[fingerprint][0], "other_id": identifier,
                                   "cross_split": by_digest[fingerprint][1] != split})
            else:
                by_digest[fingerprint] = (identifier, split)
    return {"train_count": len(train), "test_count": len(test), "duplicates": collisions,
            "leakage_detected": any(c["cross_split"] for c in collisions),
            "scope": "Exact pixel duplicates only; not near-duplicate detection"}
