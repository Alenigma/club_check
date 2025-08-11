from fastapi import status
import pyotp


def register(client, username, password, role="student"):
    res = client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "role": role, "full_name": username.title()},
    )
    assert res.status_code == 200, res.text
    return res.json()


def login(client, username, password):
    res = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_sections_and_attendance_flow_without_ble(client):
    teacher = register(client, "teacher", "pass", role="teacher")
    student = register(client, "student", "pass", role="student")
    t_tok = login(client, "teacher", "pass")
    s_tok = login(client, "student", "pass")

    r = client.post("/api/sections", json={"name": "Sec A"}, headers=auth_headers(t_tok))
    assert r.status_code == 200, r.text
    section = r.json()

    r = client.post(f"/api/sections/{section['id']}/teachers/{teacher['id']}", headers=auth_headers(t_tok))
    assert r.status_code == 200, r.text
    r = client.post(f"/api/sections/{section['id']}/students/{student['id']}", headers=auth_headers(t_tok))
    assert r.status_code == 200, r.text

    r = client.post(f"/api/teacher/master-qr/enable/{teacher['id']}", headers=auth_headers(t_tok))
    assert r.status_code == 200, r.text
    secret = r.json()["master_qr_secret"]

    r = client.post(
        f"/api/attendance/scan-lecture?secret={secret}&student_id={student['id']}&section_id={section['id']}",
        headers=auth_headers(s_tok),
    )
    assert r.status_code == 200, r.text

    r = client.get("/api/attendance/count", headers=auth_headers(s_tok))
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_student_qr_totp_scan_by_teacher(client):
    teacher = register(client, "t2", "pass", role="teacher")
    student = register(client, "s2", "pass", role="student")
    t_tok = login(client, "t2", "pass")
    s_tok = login(client, "s2", "pass")

    r = client.post("/api/sections", json={"name": "Sec B"}, headers=auth_headers(t_tok))
    section = r.json()
    client.post(f"/api/sections/{section['id']}/teachers/{teacher['id']}", headers=auth_headers(t_tok))
    client.post(f"/api/sections/{section['id']}/students/{student['id']}", headers=auth_headers(t_tok))

    r = client.get(f"/api/student/qr-token/{student['id']}", headers=auth_headers(s_tok))
    assert r.status_code == 200, r.text
    token = r.json()["token"]

    r = client.post(
        f"/api/attendance/scan-student?token={token}&section_id={section['id']}",
        headers=auth_headers(t_tok),
    )
    assert r.status_code == 200, r.text

