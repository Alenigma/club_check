import pytest


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


def test_ble_check_optional_off(client, monkeypatch):
    monkeypatch.setenv("CLUB_CHECK_ENABLE_BLE_CHECK", "false")
    import importlib
    import app.config as cfg
    importlib.reload(cfg)

    teacher = register(client, "tb", "pass", role="teacher")
    student = register(client, "sb", "pass", role="student")
    t_tok = login(client, "tb", "pass")
    s_tok = login(client, "sb", "pass")

    r = client.post("/api/sections", json={"name": "BLE-off"}, headers=auth_headers(t_tok))
    section = r.json()
    client.post(f"/api/sections/{section['id']}/teachers/{teacher['id']}", headers=auth_headers(t_tok))
    client.post(f"/api/sections/{section['id']}/students/{student['id']}", headers=auth_headers(t_tok))
    r = client.post(f"/api/teacher/master-qr/enable/{teacher['id']}", headers=auth_headers(t_tok))
    secret = r.json()["master_qr_secret"]

    r = client.post(
        f"/api/attendance/scan-lecture?secret={secret}&student_id={student['id']}&section_id={section['id']}",
        headers=auth_headers(s_tok),
    )
    assert r.status_code == 200, r.text


def test_ble_check_enabled_requires_beacon(client, monkeypatch):
    monkeypatch.setenv("CLUB_CHECK_ENABLE_BLE_CHECK", "true")
    import importlib
    import app.config as cfg
    importlib.reload(cfg)

    teacher = register(client, "tb2", "pass", role="teacher")
    student = register(client, "sb2", "pass", role="student")
    t_tok = login(client, "tb2", "pass")
    s_tok = login(client, "sb2", "pass")

    r = client.post("/api/sections", json={"name": "BLE-on"}, headers=auth_headers(t_tok))
    section = r.json()
    client.post(f"/api/sections/{section['id']}/teachers/{teacher['id']}", headers=auth_headers(t_tok))
    client.post(f"/api/sections/{section['id']}/students/{student['id']}", headers=auth_headers(t_tok))
    r = client.post(f"/api/teacher/master-qr/enable/{teacher['id']}", headers=auth_headers(t_tok))
    secret = r.json()["master_qr_secret"]

    r = client.post(
        f"/api/attendance/scan-lecture?secret={secret}&student_id={student['id']}&section_id={section['id']}",
        headers=auth_headers(s_tok),
    )
    assert r.status_code == 400

    r = client.post(
        f"/api/sections/{section['id']}/beacons",
        json={"section_id": section['id'], "beacon_id": "beacon-xyz"},
        headers=auth_headers(t_tok),
    )
    assert r.status_code == 200

    r = client.post(
        f"/api/attendance/scan-lecture?secret={secret}&student_id={student['id']}&section_id={section['id']}&beacon_id=beacon-xyz",
        headers=auth_headers(s_tok),
    )
    assert r.status_code == 200, r.text


