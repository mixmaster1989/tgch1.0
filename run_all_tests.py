#!/usr/bin/env python
import pytest
import sys
import os

if __name__ == "__main__":
    # Запускаем все тесты из директории tests
    pytest.main(["-v", "tests"])