class NotValueInTokenIdError(Exception):
    def __str__(self):
        return f'Отсутствует обязательная переменная окружения:'


class EmptyAPIResponseError(Exception):
    def __str__(self):
        return f"ответ от API не содержит ключей'"


class OtherDataType(Exception):
    def __init__(self, type):
        self.type = type

    def __str__(self):
        return f"ответ от API возвращает не список, а {self.type}"


class StatusCodeIsNot200(Exception):
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code

    def __str__(self):
        message = (f"Сбой в работе программы: "
                   f"Эндпоинт {self.url} недоступен. "
                   f"Код ответа API: {self.status_code}")
        return message


class EndpointNotWorking(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        message = f"Сбой при обращение к эндпоинту - {self.error}"
        return message


class UndocumentedStatus(Exception):
    def __init__(self, status):
        self.status = status

    def __str__(self):
        return (f"недокументированный статус '{self.status}' "
                f"домашней работы, обнаруженный в ответе API")
