# Gate Validation Strategy

## Problem

OCR plate detection is never 100% accurate. Common issues:
- Partial read: "6797" instead of "F 6797 OB"
- Misread chars: "F 6797 08" instead of "F 6797 OB"
- No read at all (blur, rain, night)

## Solution: Fuzzy Matching + Multi-Layer Validation

### Strategy: RFID Primary, Plate Secondary

```
┌─────────────────────────────────────────────────┐
│              Vehicle arrives at gate             │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼────────┐
         │   RFID Scanned? │
         └───┬─────────┬───┘
           YES         NO
             │           │
    ┌────────▼──┐   ┌───▼──────────┐
    │ Validate  │   │ Plate OCR    │
    │ RFID card │   │ Detection    │
    └────┬──────┘   └───┬──────────┘
         │              │
         │         ┌────▼──────────┐
         │         │ Fuzzy Match   │
         │         │ against DB    │
         │         └───┬───────────┘
         │             │
    ┌────▼─────────────▼───┐
    │  Check dues status   │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │  GRANT / DENY access │
    └──────────────────────┘
```

### Fuzzy Plate Matching Algorithm

Instead of exact match, use similarity scoring:

```python
def fuzzy_plate_match(detected_plate, db_plates, threshold=0.6):
    """
    Match detected plate against database using multiple strategies.
    Returns best match if score >= threshold.
    """
    detected_normalized = normalize(detected_plate)  # remove spaces, uppercase
    
    candidates = []
    for db_plate in db_plates:
        db_normalized = normalize(db_plate)
        
        # Strategy 1: Exact match
        if detected_normalized == db_normalized:
            return db_plate, 1.0
        
        # Strategy 2: Contains match (partial read)
        # "6797" is contained in "F6797OB"
        if detected_normalized in db_normalized:
            score = len(detected_normalized) / len(db_normalized)
            candidates.append((db_plate, score))
            continue
        
        # Strategy 3: Levenshtein distance
        # "F6797O8" vs "F6797OB" = distance 1
        distance = levenshtein(detected_normalized, db_normalized)
        max_len = max(len(detected_normalized), len(db_normalized))
        score = 1 - (distance / max_len)
        candidates.append((db_plate, score))
    
    # Return best match above threshold
    if candidates:
        best = max(candidates, key=lambda x: x[1])
        if best[1] >= threshold:
            return best
    
    return None, 0
```

### Matching Thresholds

| Scenario | Threshold | Action |
|----------|-----------|--------|
| Exact match | 1.0 | Auto-open gate |
| High confidence (1 char diff) | >= 0.85 | Auto-open gate |
| Medium confidence (partial read) | >= 0.6 | Auto-open + log for review |
| Low confidence | < 0.6 | Alert security, don't open |
| No match at all | 0 | Treat as guest/unknown |

### Multi-Read Consensus

Don't decide on single OCR read. Take multiple reads and vote:

```python
def gate_decision(reads, db_plates):
    """
    Take 3-5 OCR reads, find consensus.
    """
    matches = {}
    for read in reads:
        plate, score = fuzzy_plate_match(read, db_plates)
        if plate:
            matches[plate] = matches.get(plate, [])
            matches[plate].append(score)
    
    # Best match = highest average score with most votes
    if matches:
        best = max(matches.items(), key=lambda x: (len(x[1]), sum(x[1])/len(x[1])))
        plate = best[0]
        avg_score = sum(best[1]) / len(best[1])
        votes = len(best[1])
        
        if votes >= 2 and avg_score >= 0.6:
            return plate, "GRANT"
        elif votes >= 1 and avg_score >= 0.85:
            return plate, "GRANT"
    
    return None, "DENY"
```

### Recommended Gate Modes

| Mode | How it works | Best for |
|------|-------------|----------|
| `rfid_only` | Only RFID, no plate check | Simple, fast, reliable |
| `rfid_and_plate` | RFID required + plate as confirmation | High security |
| `plate_only` | Only plate OCR | No RFID hardware needed |
| `rfid_or_plate` | Either one works | Best UX (forgot card? plate works) |
| `open` | Always open | Maintenance/events |

### Recommended: `rfid_or_plate` mode

- RFID = instant, 100% reliable (primary)
- Plate OCR = backup when forgot card
- If plate partial match (score 0.6-0.85) + RFID fail → ask security
- Log everything for audit

### Hardware Recommendations

For reliable plate OCR at gate:
- Camera: 2MP+ with IR night vision, fixed mount 1-2m from plate
- Angle: straight-on or max 15° angle
- Lighting: IR illuminator or dedicated plate light
- Resolution: plate should occupy at least 30% of frame width
- Brands: Hikvision DS-2CD series, Dahua IPC-HFW series (native RTSP)

### Database Index for Fuzzy Search

```javascript
// For partial/contains matching, store normalized plate
db.vehicles.createIndex({ "plate_number_normalized": 1 })

// Also store individual parts for partial matching
// "F6797OB" -> prefix: "F", number: "6797", suffix: "OB"
db.vehicles.createIndex({ "plate_parts.number": 1 })
```

### Summary

Don't rely on perfect OCR. Build the system to handle imperfect reads:
1. Use RFID as primary (100% reliable)
2. Plate OCR as secondary/backup
3. Fuzzy match against known plates in DB
4. Multi-read consensus (3+ reads before deciding)
5. Log everything, alert security on low confidence
