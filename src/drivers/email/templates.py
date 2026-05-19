"""
Email HTML templates for notifications.
"""


def dues_reminder_template(
    name: str, periods: list, total_amount: int, due_day: int
) -> str:
    """Generate HTML email for dues reminder."""
    period_rows = ""
    for p in sorted(periods):
        period_rows += f"<tr><td style='padding:8px;border:1px solid #ddd'>{p}</td></tr>\n"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
  <div style="background:#f8f9fa;border-radius:8px;padding:24px;margin-bottom:20px">
    <h2 style="color:#333;margin-top:0">🏠 Pengingat Pembayaran Iuran</h2>
    <p>Yth. <strong>{name}</strong>,</p>
    <p>Berikut adalah tagihan iuran yang belum dibayar:</p>

    <table style="width:100%;border-collapse:collapse;margin:16px 0">
      <thead>
        <tr style="background:#e9ecef">
          <th style="padding:8px;border:1px solid #ddd;text-align:left">Periode</th>
        </tr>
      </thead>
      <tbody>
        {period_rows}
      </tbody>
    </table>

    <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:12px;margin:16px 0">
      <strong>Total Tagihan: Rp {total_amount:,.0f}</strong>
    </div>

    <p>Mohon segera melakukan pembayaran sebelum tanggal <strong>{due_day}</strong> setiap bulannya.</p>
    <p>Pembayaran dapat dilakukan via transfer atau langsung ke Pak RT.</p>

    <hr style="border:none;border-top:1px solid #ddd;margin:20px 0">
    <p style="color:#666;font-size:12px">
      Email ini dikirim otomatis oleh sistem keamanan perumahan.<br>
      Jika sudah membayar, mohon abaikan email ini.
    </p>
  </div>
</body>
</html>"""
