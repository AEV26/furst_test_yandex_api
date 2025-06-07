import pytest
import requests
import allure
from allure_commons.types import Severity, AttachmentType
from faker import Faker
from config import TASKS_API_URL, AUTH_TOKEN, ORG_ID

fake = Faker()

# Конфигурация заголовков
HEADERS = {
    "Authorization": f"OAuth {AUTH_TOKEN}",
    "X-Cloud-Org-ID": ORG_ID,
    "Content-Type": "application/json"
}
EMPTY_HEADERS= {
    "Content-Type": "application/json"
}


@allure.title("Создание новой задачи")
@allure.severity(Severity.BLOCKER)
@allure.feature("API Yandex Tracker")
@allure.story("Метод создания задачи")
@pytest.mark.parametrize("issue_data", [
    pytest.param(
        {
            "queue": "TESTAEV",
            "summary": fake.sentence(),
            "description": fake.text()
        },
        id="minimal_fields"
    ),
    pytest.param(
        {
            "queue": "TESTAEV",
            "summary": fake.sentence(),
            "description": fake.text(),
            "type": "task",
            "priority": "normal"
        },
        id="all_basic_fields"
    ),
    pytest.param(
        {
            "queue": "TESTAEV",
            "summary": "XSS Test <script>alert(1)</script>",
            "description": "HTML: <b>bold</b>"
        },
        id="html_injection_check"
    )
])
def test_create_issue(issue_data):
    with allure.step("Подготовка тестовых данных"):
        allure.attach(
            name="Request Payload",
            body=str(issue_data),
            attachment_type=AttachmentType.JSON
        )

    with allure.step("Отправка запроса на создание задачи"):
        response = requests.post(
            TASKS_API_URL,
            headers=HEADERS,
            json=issue_data,
            timeout=10
        )

        allure.attach(
            name="Response",
            body=response.text,
            attachment_type=AttachmentType.JSON
        )

    with allure.step("Проверка статус-кода"):
        assert response.status_code == 201, (
            f"Ожидался код 201, получен {response.status_code}. "
            f"Response: {response.text}"
        )

    with allure.step("Валидация ответа"):
        created_issue = response.json()

        assert "id" in created_issue, "Ответ не содержит ID задачи"
        assert "key" in created_issue, "Ответ не содержит ключа задачи"
        assert created_issue["summary"] == issue_data["summary"]

        allure.attach(
            name="Created Issue",
            body=str(created_issue),
            attachment_type=AttachmentType.JSON
        )

    with allure.step("Проверка через GET-запрос"):
        issue_id = created_issue["id"]
        get_response = requests.get(
            f"{TASKS_API_URL}/{issue_id}",
            headers=HEADERS,
            timeout=5
        )

        assert get_response.status_code == 200
        assert get_response.json()["id"] == issue_id


@allure.title("Негативные сценарии создания задачи")
@allure.severity(Severity.CRITICAL)
@pytest.mark.parametrize("invalid_data,expected_status,error_key", [
    pytest.param(
        {"summary": "Missing queue"},
        400,
        "errors",
        id="missing_queue"
    ),
    pytest.param(
        {"queue": "TESTAEV"},
        400,
        "errors",
        id="missing_summary"
    ),
    pytest.param(
        {"queue": "NONEXISTENT", "summary": "Test"},
        404,
        "errorMessages",
        id="nonexistent_queue"
    ),
    pytest.param(
        None,
        400,
        "errors",
        id="null_payload"
    )
])
def test_create_issue_negative(invalid_data, expected_status, error_key):
    with allure.step("Отправка невалидного запроса"):
        response = requests.post(
            TASKS_API_URL,
            headers=HEADERS,
            json=invalid_data,
            timeout=5
        )

        allure.attach(
            name="Response",
            body=response.text,
            attachment_type=AttachmentType.JSON
        )

    with allure.step("Проверка ошибки"):
        assert response.status_code == expected_status
        error_response = response.json()
        assert error_key in error_response
        assert len(error_response[error_key]) > 0


@allure.title("Проверка авторизации")
@allure.severity(Severity.CRITICAL)
def test_unauthorized_create():
    with allure.step("Запрос без авторизации"):
        response = requests.post(
            TASKS_API_URL,
            headers = EMPTY_HEADERS,
            json={"queue": "TESTAEV", "summary": "Unauthorized test"}
        )

        assert response.status_code == 401
        assert response.text == "Authorization required"