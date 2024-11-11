from tqdm import tqdm


def pytest_collection_modifyitems(session, config, items):
    """Добавляем прогресс-бар для тестов."""
    total_tests = len(items)
    for item in tqdm(
        items,
        total=total_tests,
        desc="Running tests",
        unit="test"
    ):
        pass
