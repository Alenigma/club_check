from fastapi import status


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


def test_register_and_login_student(client):
    register(client, "student", "pass", role="student")
    token = login(client, "student", "pass")
    assert token


def test_rbac_teacher_only_endpoints(client):
    register(client, "student", "pass", role="student")
    register(client, "teacher", "pass", role="teacher")
    st = login(client, "student", "pass")
    tch = login(client, "teacher", "pass")

    # student cannot list users
    r = client.get("/api/users/", headers=auth_headers(st))
    assert r.status_code == status.HTTP_403_FORBIDDEN

    # teacher can
    r = client.get("/api/users/", headers=auth_headers(tch))
    assert r.status_code == 200


