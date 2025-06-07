import pytest
import requests
import allure
from allure_commons.types import Severity, AttachmentType
from config import TASKS_API_URL, AUTH_TOKEN, ORG_ID

# Конфигурация заголовков
HEADERS = {
    "Authorization": f"OAuth {AUTH_TOKEN}",
    "X-Cloud-Org-ID": ORG_ID,
    "Content-Type": "application/json"
}


@pytest.fixture
def create_test_issue():
    """Фикстура для создания тестовой задачи"""
    issue_data = {
        "queue": "TESTAEV",
        "summary": "Test issue for GET method",
        "description": "This issue will be fetched in tests"
    }
    response = requests.post(
        TASKS_API_URL,
        headers=HEADERS,
        json=issue_data
    )
    issue_id = response.json()["id"]
    yield issue_id
    # Удаление задачи после теста
    #requests.delete(f"{TASKS_API_URL}/{issue_id}", headers=HEADERS)


@allure.title("Получение существующей задачи")
@allure.severity(Severity.CRITICAL)
@allure.feature("API Yandex Tracker")
@allure.story("Метод получения задачи")
def test_get_issue_success(create_test_issue):
    issue_id = create_test_issue

    with allure.step(f"Отправка GET запроса для задачи {issue_id}"):
        response = requests.get(
            f"{TASKS_API_URL}/{issue_id}",
            headers=HEADERS
        )

        allure.attach(
            name="Request Details",
            body=f"URL: {TASKS_API_URL}/{issue_id}\nMethod: GET",
            attachment_type=AttachmentType.TEXT
        )

        allure.attach(
            name="Response",
            body=response.text,
            attachment_type=AttachmentType.JSON
        )

    with allure.step("Проверка ответа"):
        assert response.status_code == 200
        issue = response.json()

        assert issue["id"] == issue_id
        assert issue["summary"] == "Test issue for GET method"
        assert issue["description"] == "This issue will be fetched in tests"
        assert "createdAt" in issue
        assert "updatedAt" in issue


@allure.title("Попытка получения несуществующей задачи")
@allure.severity(Severity.NORMAL)
def test_get_nonexistent_issue():
    nonexistent_id = "6242ed6156158c35daaa5b56"

    with allure.step(f"Запрос несуществующей задачи {nonexistent_id}"):
        response = requests.get(
            f"{TASKS_API_URL}/{nonexistent_id}",
            headers=HEADERS
        )

        allure.attach(
            name="Response",
            body=response.text,
            attachment_type=AttachmentType.JSON
        )

        assert response.status_code == 404
        assert "errorMessages" in response.json()
        assert "Задача не существует." in response.json()["errorMessages"][0]


@allure.title("Получение задачи без авторизации")
@allure.severity(Severity.CRITICAL)
def test_get_issue_unauthorized(create_test_issue):
    issue_id = create_test_issue

    with allure.step("Запрос без заголовков авторизации"):
        response = requests.get(
            f"{TASKS_API_URL}/{issue_id}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 401
        assert response.text == "Authorization required"


@allure.title("Получение задачи с неверным Org-ID")
@allure.severity(Severity.NORMAL)
def test_get_issue_wrong_org_id(create_test_issue):
    issue_id = create_test_issue

    with allure.step("Запрос с неверным X-Org-ID"):
        wrong_headers = HEADERS.copy()
        wrong_headers["X-Cloud-Org-ID"] = "wrong_org_id"

        response = requests.get(
            f"{TASKS_API_URL}/{issue_id}",
            headers=wrong_headers
        )

        assert response.status_code == 403
        assert "errorMessages" in response.json()
        assert "Organization is not available, not ready or not found" in response.json()["errorMessages"][0]


@allure.title("Получение задачи с расширенными полями")
@allure.severity(Severity.NORMAL)
def test_get_issue_with_expand(create_test_issue):
    #issue_id = create_test_issue

    with allure.step("Запрос с expand"):
        response = requests.get(
            f"{TASKS_API_URL}/TESTAEV-80?expand=attachments",
            headers=HEADERS
        )

        assert response.status_code == 200
        issue = response.json()
        assert "attachments" in issue