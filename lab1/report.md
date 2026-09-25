# Отчёт по лабораторной работе 1

**Дисциплина:** Анализ и оптимизация программного кода для ИБ
**Тема:** Настройка рабочей среды для анализа и оптимизации кода
**ФИО:** ______________________
**Группа:** ____________________
**Дата:** ______________________

## 1. Цель работы
Настроить изолированную среду для статического анализа Python-кода,
освоить Bandit / Ruff / pip-audit, выявить и устранить типовые дефекты
безопасности на учебном примере.

## 2. Рабочая среда
- Среда: GitHub Codespaces (Ubuntu Linux)
- Python 3.1x
- Редактор: VS Code в браузере
- Виртуальное окружение: .venv (создано через python -m venv .venv)
- Инструменты: bandit, ruff, pip-audit
- Git: 2.4x

## 3. Выполненные команды
| Команда | Назначение |
|---------|-----------|
| git init | инициализация репозитория |
| python -m venv .venv | создание изолированного окружения |
| source .venv/bin/activate | активация окружения |
| pip install bandit ruff pip-audit | установка инструментов анализа |
| python vulnerable_demo.py | локальный запуск уязвимого примера |
| ruff check . | анализ качества кода |
| bandit -r . -x ./.venv -f txt | текстовый SAST-отчёт |
| bandit -r . -x ./.venv -f json -o bandit_report.json | машинный отчёт |
| python -m pip freeze > requirements.txt | фиксация зависимостей |
| pip-audit -r requirements.txt | SCA-аудит зависимостей |
| git commit / push | фиксация состояния проекта |

## 4. Результаты Ruff
Ruff обнаружил замечание I001 (несортированные импорты в vulnerable_demo.py).
Это замечание качества кода, не связанное с безопасностью. После его
устранения (или фиксации) других замечаний Ruff не выявил.

## 5. Результаты Bandit (минимум 5 проблем безопасности)
| # | Проблема | CWE | Уровень | Место в коде |
|---|----------|-----|---------|--------------|
| 1 | Hardcoded password | CWE-259 | High | ADMIN_PASSWORD = "admin123" |
| 2 | SQL Injection | CWE-89 | Medium | find_user(): конкатенация строк |
| 3 | eval() | CWE-95 | Medium | calculate(): eval(expression) |
| 4 | Command Injection | CWE-78 | High | run_diagnostic(): os.system |
| 5 | pickle.loads | CWE-502 | Medium | load_profile() |
| 6 | MD5 для пароля | CWE-327 | High | weak_password_hash() |
| 7 | Predictable token | CWE-330 | Medium | generate_token() |

После применения безопасной версии secure_demo.py повторный запуск Bandit
не выявил критичных (High/Medium) проблем безопасности.

## 6. Сравнение vulnerable / secure
| Проблема | vulnerable_demo.py | secure_demo.py |
|----------|--------------------|----------------|
| Пароль | ADMIN_PASSWORD = "admin123" | секрет хранится вне кода |
| SQL | конкатенация строк | параметризованный запрос (?) |
| eval | eval(expression) | ast + whitelist операторов |
| Команды | os.system + конкатенация | subprocess.run + allowlist |
| pickle | pickle.loads() | удалено |
| Хеш | MD5 | PBKDF2-HMAC-SHA256 + соль |
| Токен | random.randint | secrets.token_urlsafe |

## 7. Результаты pip-audit
<вставить вывод pip-audit -r requirements.txt из pip_audit_report.txt>

SCA проверяет сторонние библиотеки на известные CVE, тогда как SAST
анализирует наш собственный исходный код. Это дополняющие подходы.

## 8. Выводы
1. Изолированная среда (.venv) обеспечивает воспроизводимость анализа
   и не смешивает зависимости с системными.
2. Git фиксирует состояние «до/после» и доказывает факт устранения
   уязвимостей.
3. SAST (Bandit) находит опасные паттерны без запуска кода.
4. Ruff дополняет Bandit: качество кода напрямую влияет на безопасность.
5. SCA (pip-audit) закрывает класс рисков в сторонних пакетах.
6. Замена MD5 -> PBKDF2 и random -> secrets резко повышает стойкость.

## 9. Приложения
- vulnerable_demo.py
- secure_demo.py
- bandit_report.json
- requirements.txt
