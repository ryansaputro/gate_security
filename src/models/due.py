from entities.due import Due

COLLECTION_NAME = "dues"


def to_document(entity: Due) -> dict:
    doc = {
        "familyId": entity.family_id,
        "houseId": entity.house_id,
        "period": entity.period,
        "year": entity.year,
        "month": entity.month,
        "type": entity.type,
        "amount": entity.amount,
        "paidAmount": entity.paid_amount,
        "status": entity.status,
        "paidAt": entity.paid_at,
        "paymentMethod": entity.payment_method,
        "receiptNumber": entity.receipt_number,
        "collectorName": entity.collector_name,
        "dueDate": entity.due_date,
        "notes": entity.notes,
        "createdAt": entity.created_at,
        "updatedAt": entity.updated_at,
    }
    if entity.id:
        doc["_id"] = entity.id
    return doc


def from_document(doc: dict) -> Due:
    return Due(
        id=str(doc.get("_id", "")),
        family_id=doc.get("familyId", ""),
        house_id=doc.get("houseId", ""),
        period=doc.get("period", ""),
        year=doc.get("year", 0),
        month=doc.get("month", 0),
        type=doc.get("type", ""),
        amount=doc.get("amount", 0),
        paid_amount=doc.get("paidAmount", 0),
        status=doc.get("status", "unpaid"),
        paid_at=doc.get("paidAt"),
        payment_method=doc.get("paymentMethod", ""),
        receipt_number=doc.get("receiptNumber", ""),
        collector_name=doc.get("collectorName", ""),
        due_date=doc.get("dueDate"),
        notes=doc.get("notes", ""),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )
