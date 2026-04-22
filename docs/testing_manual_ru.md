# Практический Мануал По Тестированию

## Для чего этот файл

Это человеческая инструкция по запуску и проверке `local-stt-diarization` на Windows. Она написана не для агентов, а для ручной работы: поднять окружение, запустить проект, проверить основные сценарии и зафиксировать результат.

## Где работать

Рабочая папка проекта:

```powershell
cd C:\Users\Tykhon\Desktop\code_base\agents-hub\sandbox\local-stt-diarization
```

Все команды ниже предполагают, что ты находишься именно в этой директории.

## Что понадобится заранее

- Windows
- Python 3.10+
- `ffmpeg` в `PATH`
- доступ в интернет для первой загрузки моделей
- по возможности NVIDIA CUDA, если хочешь проверять GPU-режим
- для diarization при необходимости токен Hugging Face

## Быстрая схема тестирования

Порядок такой:

1. Поднять окружение
2. Проверить базовую команду и CLI
3. Прогнать короткий smoke test без optional stages
4. Проверить alignment отдельно
5. Проверить diarization отдельно
6. Проверить realistic single-file run
7. Зафиксировать результат

## Шаг 1. Поднять окружение

Создание и активация виртуального окружения:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Установка проекта:

```powershell
pip install -e .
```

Проверка Python:

```powershell
python --version
```

Проверка `ffmpeg`:

```powershell
ffmpeg -version
```

Проверка CLI:

```powershell
local-stt-diarization --help
```

Если `local-stt-diarization --help` не работает, можно временно запускать так:

```powershell
python -m local_stt_diarization.cli --help
```

## Шаг 2. Подготовить тестовые файлы

Нужны 3 типа файлов:

- короткий простой файл для smoke test
- файл для проверки alignment и diarization
- один реалистичный длинный файл для acceptance

Лучше держать их вне git или в локальной папке, например:

```powershell
mkdir local-test-inputs
```

Примеры путей дальше:

- `local-test-inputs\short.wav`
- `local-test-inputs\interview.wav`
- `local-test-inputs\long_session.m4a`

Не коммить реальные записи в репозиторий.

## Шаг 3. Smoke Test Без Alignment И Diarization

Это первый и самый важный прогон. Он показывает, что основной transcript path живой.

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-smoke --disable-alignment --disable-diarization
```

Если через entrypoint не запускается:

```powershell
$env:PYTHONPATH=".\src"
python -m local_stt_diarization.cli ".\local-test-inputs\short.wav" --output-dir .\output\manual-smoke --disable-alignment --disable-diarization
```

Что проверить после прогона:

- в консоли видны сообщения по стадиям
- создался `json`
- создался `txt`
- создался `md`
- появился checkpoint в `output\manual-smoke\checkpoints\`, если run шёл достаточно долго
- команда завершилась без падения

Проверка файлов:

```powershell
Get-ChildItem .\output\manual-smoke
```

Посмотреть JSON:

```powershell
Get-Content .\output\manual-smoke\short.json
```

Что должно быть по смыслу:

- есть `schema_version`
- есть `source`
- есть `segments`
- есть `stage_statuses`
- transcript экспортировался успешно

Если появился файл в `checkpoints`, это нормально: это промежуточный operational artifact, а не финальный результат вместо обычного `json`.

## Шаг 4. Проверка Alignment

Теперь проверяем optional stage, который не должен ломать экспорт.

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-alignment --disable-diarization
```

Если alignment сработал:

- в `stage_statuses` у `alignment` будет `completed`

Если alignment не сработал:

- итоговый transcript всё равно должен экспортироваться
- в `warnings` или `stage_statuses` должна быть честная деградация

Посмотреть JSON:

```powershell
Get-Content .\output\manual-alignment\short.json
```

## Шаг 5. Проверка Diarization

Теперь проверяем diarization отдельно.

Если нужен токен:

```powershell
$env:HF_TOKEN="твой_токен"
```

Или:

```powershell
$env:HUGGINGFACE_HUB_TOKEN="твой_токен"
```

Команда:

```powershell
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-diarization --disable-alignment
```

Что проверять:

- transcript экспортировался
- diarization либо сработал, либо честно деградировал
- `speaker` не должен проставляться агрессивно в сомнительных местах

Посмотреть JSON:

```powershell
Get-Content .\output\manual-diarization\interview.json
```

Ищи:

- `diarization_failed`
- `diarization_unavailable`
- `speaker_assignment_ambiguous`

Это не обязательно ошибка проекта. Это может быть нормальное fail-soft поведение.

## Шаг 6. Проверка Speaker Hints

Проверка с точным количеством спикеров:

```powershell
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-speakers-exact --speakers 2
```

Проверка с диапазоном:

```powershell
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-speakers-range --min-speakers 2 --max-speakers 4
```

Что проверять:

- команда доходит до конца
- speaker hints реально влияют на diarization run
- при сомнительном результате `speaker` всё равно может остаться пустым

## Шаг 7. Проверка Long-Form Acceptance

Сначала безопасный прогон без optional stages:

```powershell
local-stt-diarization ".\local-test-inputs\long_session.m4a" --output-dir .\output\manual-long-base --disable-alignment --disable-diarization
```

Потом полный прогон:

```powershell
local-stt-diarization ".\local-test-inputs\long_session.m4a" --output-dir .\output\manual-long-full
```

Что фиксировать во время long run:

- появляются ли сообщения `prepare`, `transcription`, `alignment`, `diarization`, `export`
- сколько длится запись
- сколько длился сам прогон
- был ли первый download моделей
- не упёрся ли запуск в RAM/VRAM
- завершился ли transcript export
- были ли warnings по alignment
- были ли warnings по diarization
- полезны ли speaker labels на глаз
- появлялся ли checkpoint-файл по пути `output\...\checkpoints\`

## Шаг 8. Если Хочешь Проверить CPU-Режим

Это полезно для отладки окружения.

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-cpu --device cpu --compute-type int8 --disable-alignment --disable-diarization
```

Если CPU-режим работает, а CUDA-режим нет, проблема почти наверняка в локальном GPU/Torch/CUDA окружении, а не в базовом transcript pipeline.

## Шаг 9. Что Считать Успешным Результатом

Минимально успешное тестирование:

- CLI запускается
- короткий smoke test проходит
- во время run видны признаки жизни по стадиям
- transcript экспортируется в `json`, `txt`, `md`
- optional stages не ломают обязательный transcript path
- деградации отражаются честно через warnings и statuses

Хорошее тестирование:

- прошёл хотя бы один multi-speaker файл
- проверены speaker hints
- прошёл хотя бы один длинный realistic single-file run

## Что Делать Если Что-То Падает

Проверять по порядку:

1. Активировано ли правильное `.venv`
2. Работает ли `ffmpeg -version`
3. Работает ли `local-stt-diarization --help`
4. Идёт ли короткий smoke test без alignment и diarization
5. Работает ли тот же запуск через `--device cpu`
6. Только потом проверять alignment и diarization

Если diarization ломается, это не повод считать весь проект сломанным, если transcript при этом всё равно экспортируется.

## Короткий Чеклист Команд

Поднять окружение:

```powershell
cd C:\Users\Tykhon\Desktop\code_base\agents-hub\sandbox\local-stt-diarization
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
ffmpeg -version
local-stt-diarization --help
```

Smoke:

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-smoke --disable-alignment --disable-diarization
```

Alignment:

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-alignment --disable-diarization
```

Diarization:

```powershell
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-diarization --disable-alignment
```

Speaker hints:

```powershell
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-speakers-exact --speakers 2
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-speakers-range --min-speakers 2 --max-speakers 4
```

Long-form:

```powershell
local-stt-diarization ".\local-test-inputs\long_session.m4a" --output-dir .\output\manual-long-base --disable-alignment --disable-diarization
local-stt-diarization ".\local-test-inputs\long_session.m4a" --output-dir .\output\manual-long-full
```

## Шаблон Для Ручной Фиксации Результатов

Можно просто копировать этот блок и заполнять:

```text
Файл:
Длительность:
Команда:
Окружение: CPU / CUDA
First-run download: да / нет
Итог: success / fail
JSON/TXT/MD создались: да / нет
Checkpoint создался: да / нет
Alignment: completed / skipped / degraded
Diarization: completed / skipped / degraded
Warnings:
Наблюдения по качеству:
```
