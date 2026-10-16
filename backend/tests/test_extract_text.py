def make_pdf(lines: list[str]) -> bytes:
    """Build a tiny one-page PDF with real text objects (no extra dependencies needed)."""
    text_ops = " ".join(f"({line}) Tj 0 -16 Td" for line in lines)
    stream = f"BT /F1 12 Tf 72 720 Td {text_ops} ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref_at = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref_at)
    return bytes(out)


def test_extract_text_from_pdf(client):
    pdf = make_pdf(["Jane Doe", "Python and React developer"])
    response = client.post("/api/extract-text", files={"file": ("resume.pdf", pdf, "application/pdf")})

    assert response.status_code == 200
    body = response.json()
    assert body["pages"] == 1
    assert "Jane Doe" in body["text"]
    assert "Python and React developer" in body["text"]


def test_extract_text_rejects_non_pdf(client):
    response = client.post("/api/extract-text", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 415


def test_extract_text_rejects_corrupt_pdf(client):
    response = client.post("/api/extract-text", files={"file": ("bad.pdf", b"not a pdf", "application/pdf")})
    assert response.status_code == 422
