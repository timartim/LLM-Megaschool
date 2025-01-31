import requests
import argparse
import time
from typing import List, Dict
import concurrent.futures

TEST_CASES = [
    {
        "id": 1,
        "query": "В каком году Университет ИТМО выиграл свой первый чемпионат мира по программированию ACM ICPC?\n1. 1999\n2. 2004\n3. 2012\n4. 2017",
        "expected_answer": 2
    },
    {
        "id": 2,
        "query": "Сколько раз Университет ИТМО становился чемпионом мира по программированию ACM ICPC?\n1. 7\n2. 9\n3. 5\n4. 3",
        "expected_answer": 1
    },
    {
        "id": 3,
        "query": "В каком рейтинге (2023) ИТМО занял 400+ позицию?\n1. ARWU\n2. THE\n3. QS\n4. U.S. News",
        "expected_answer": 1
    },
    {
        "id": 4,
        "query": "Какой факультет ИТМО занимается фотоникой?\n1. ФПМИ\n2. ФТМИ\n3. ФОПФ\n4. ЛФТ",
        "expected_answer": 3
    },
    {
        "id": 5,
        "query": "В каком году ИТМО получил статус университета?\n1. 1900\n2. 1930\n3. 1992\n4. 2000",
        "expected_answer": 3
    },
    {
        "id": 6,
        "query": "Какой номер в рейтинге QS BRICS 2022 у ИТМО?\n1. 14\n2. 25\n3. 30\n4. 7",
        "expected_answer": 1
    },
    {
        "id": 7,
        "query": "Сколько научных лабораторий в ИТМО?\n1. 50\n2. 100\n3. 200\n4. 150",
        "expected_answer": 3
    },
    {
        "id": 8,
        "query": "Какой язык программирования преподают на 1 курсе ФИТиП?\n1. Python\n2. Java\n3. C++\n4. Pascal",
        "expected_answer": 1
    },
    {
        "id": 9,
        "query": "Сколько кампусов у ИТМО?\n1. 1\n2. 3\n3. 5\n4. 7",
        "expected_answer": 2
    },
    {
        "id": 10,
        "query": "Какой ученый из ИТМО получил Нобелевскую премию?\n1. Алферов\n2. Иванов\n3. Петров\n4. Нет таких",
        "expected_answer": 4
    },
    {
        "id": 11,
        "query": "В каком году открылся факультет биотехнологий?\n1. 2010\n2. 2015\n3. 2020\n4. 2022",
        "expected_answer": 3
    },
    {
        "id": 12,
        "query": "Сколько студентов в ИТМО?\n1. 5000\n2. 12000\n3. 20000\n4. 30000",
        "expected_answer": 2
    },
    {
        "id": 13,
        "query": "Какой индекс цитирования у ИТМО?\n1. h-index 50\n2. h-index 100\n3. h-index 150\n4. h-index 200",
        "expected_answer": 2
    },
    {
        "id": 14,
        "query": "Какая специальность самая популярная в ИТМО?\n1. Data Science\n2. Cybersecurity\n3. Robotics\n4. Software Engineering",
        "expected_answer": 1
    },
    {
        "id": 15,
        "query": "Сколько иностранных студентов в ИТМО?\n1. 500\n2. 1500\n3. 3000\n4. 5000",
        "expected_answer": 2
    },
    {
        "id": 16,
        "query": "Какой процент выпускников ИТМО работает по специальности?\n1. 50%\n2. 70%\n3. 85%\n4. 95%",
        "expected_answer": 3
    },
    {
        "id": 17,
        "query": "В каком городе нет кампуса ИТМО?\n1. Москва\n2. Санкт-Петербург\n3. Сочи\n4. Томск",
        "expected_answer": 4
    },
    {
        "id": 18,
        "query": "Какой проект ИТМО по квантовым технологиям?\n1. РОКК\n2. QApp\n3. Фотоника\n4. Киберсердце",
        "expected_answer": 1
    },
    {
        "id": 19,
        "query": "Сколько лет учиться в магистратуре ИТМО?\n1. 1\n2. 2\n3. 3\n4. 4",
        "expected_answer": 2
    },
    {
        "id": 20,
        "query": "Какой клуб ИТМО по робототехнике?\n1. КиберКот\n2. РобоПолитех\n3. ТехноЛаб\n4. ИИКлуб",
        "expected_answer": 1
    }
]

def run_test(test_case: Dict, api_url: str) -> bool:
    """
    Выполняет один API-запрос по тестовому кейсу.
    Возвращает True, если ответ соответствует ожидаемому, иначе False.
    """
    try:
        response = requests.post(
            f"{api_url}/api/request",
            json={"id": test_case["id"], "query": test_case["query"]},
            timeout=60
        )

        if response.status_code != 200:
            print(f"Test {test_case['id']} ❌: HTTP Error {response.status_code}")
            return False

        response_data = response.json()
        received_answer = response_data.get("answer")

        if received_answer == test_case["expected_answer"]:
            print(f"Test {test_case['id']} ✅: Correct answer {received_answer}")
            return True
        else:
            print(f"Test {test_case['id']} ❌: Expected {test_case['expected_answer']}, got {received_answer}")
            return False

    except requests.Timeout:
        print(f"Test {test_case['id']} ❌: Request timeout")
    except Exception as e:
        print(f"Test {test_case['id']} ❌: Error - {str(e)}")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API Tester for ITMO Q&A System")
    parser.add_argument("--api-url", required=True, help="Base URL of the API (e.g. http://localhost:8080)")
    args = parser.parse_args()
    api_url = args.api_url.rstrip('/')

    print(f"Starting tests for API at {api_url}...\n")

    total_requests = 100
    test_queue: List[Dict] = TEST_CASES * 5

    start_time = time.perf_counter()
    success_count = 0

    max_workers = 10

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_test = {executor.submit(run_test, test_case, api_url): test_case for test_case in test_queue}

        for future in concurrent.futures.as_completed(future_to_test):
            if future.result():
                success_count += 1

    elapsed_time = time.perf_counter() - start_time
    print(f"\nResults: {success_count}/{total_requests} passed ({success_count / total_requests:.0%})")
    print(f"Total execution time: {elapsed_time:.2f} seconds")
