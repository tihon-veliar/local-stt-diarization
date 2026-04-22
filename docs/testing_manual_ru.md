# Практический Мануал По Тестированию

## Для Чего Этот Файл

Это человеческая инструкция по ручной проверке `local-stt-diarization` на Windows.
Она нужна для реальных прогонов, а не для агентных рассуждений:

- поднять окружение
- проверить guided mode и raw CLI
- убедиться, что transcript-first поведение не сломалось
- зафиксировать warnings, checkpoints и финальные артефакты

## Где Работать

```powershell
cd C:\Users\Tykhon\Desktop\code_base\agents-hub\sandbox\local-stt-diarization
```

## Что Нужно Заранее

- Windows
- Python 3.10+
- `ffmpeg` в `PATH`
- локальные тестовые аудиофайлы
- доступ в интернет для первого скачивания моделей
- при необходимости CUDA и Hugging Face token для diarization

## Быстрый Порядок Проверки

1. Поднять окружение.
2. Проверить `--help`.
3. Прогнать smoke test без optional stages.
4. Проверить guided mode.
5. Проверить raw CLI fallback.
6. Проверить realistic long-form run.
7. Зафиксировать результат.

## Шаг 1. Поднять Окружение

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python --version
ffmpeg -version
local-stt-diarization --help
```

Если entrypoint не поднимается:

```powershell
python -m local_stt_diarization.cli --help
```

## Шаг 2. Подготовить Тестовые Файлы

Держи локальные файлы вне git, например:

```powershell
mkdir local-test-inputs
mkdir input
```

Примеры:

- `local-test-inputs\short.wav`
- `local-test-inputs\interview.wav`
- `local-test-inputs\long_session.m4a`

Для guided mode скопируй один-два файла в `input\`.

## Шаг 3. Smoke Test Без Optional Stages

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-smoke --disable-alignment --disable-diarization
```

Проверить:

- stage plan печатается до начала run
- видны стадии `prepare`, `transcription`, `alignment`, `diarization`, `export`
- `alignment` и `diarization` честно видны как `skipped`
- создаётся финальный `json`
- при необходимости создаётся checkpoint в `output\manual-smoke\checkpoints\`
- run завершается без падения

## Шаг 4. Guided Mode

```powershell
local-stt-diarization --guided
```

Проверить в guided flow:

- показываются только верхнеуровневые файлы из `input\`
- путь по умолчанию идёт в `output\<input-stem>\`
- есть presets `Fast transcript`, `Full transcript + diarization`, `Safe CPU / troubleshooting`, `Custom`
- `JSON` нельзя выключить
- `TXT` и `Markdown` можно включать и выключать
- перед стартом виден run summary

Проверить после старта:

- stage plan печатается до начала обработки
- счётчики стадий стабильные: `1/5`, `2/5`, `3/5`, ...
- disabled optional stages всё равно видны как `skipped`
- warnings не пропадают
- checkpoint path виден, если checkpoint создавался
- финальные пути к артефактам видны в конце

## Шаг 5. Raw CLI Fallback

Проверка нужна, чтобы guided mode не скрывал проблемы базового pipeline.

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-raw --no-txt --no-md
```

Проверить:

- raw CLI всё ещё работает без guided prompts
- создаётся обязательный `json`
- `txt` и `md` действительно не создаются
- stage plan и warnings видны так же, как в guided run

## Шаг 6. Alignment И Diarization

Alignment:

```powershell
local-stt-diarization ".\local-test-inputs\short.wav" --output-dir .\output\manual-alignment --disable-diarization
```

Diarization:

```powershell
local-stt-diarization ".\local-test-inputs\interview.wav" --output-dir .\output\manual-diarization --disable-alignment
```

Проверить:

- transcript всё равно экспортируется
- optional stage может быть `completed`, `skipped` или `degraded`
- деградация отражается и в runtime output, и в warnings
- сомнительные speaker labels не проставляются агрессивно

## Шаг 7. Long-Form Acceptance

Сначала безопасный прогон:

```powershell
local-stt-diarization ".\local-test-inputs\long_session.m4a" --output-dir .\output\manual-long-base --disable-alignment --disable-diarization
```

Потом полный:

```powershell
local-stt-diarization ".\local-test-inputs\long_session.m4a" --output-dir .\output\manual-long-full
```

Зафиксировать:

- был ли первый download моделей
- появлялись ли stage counters на всём run
- были ли checkpoints
- дошёл ли export до конца
- какие warnings были по alignment и diarization
- хватает ли transcript completeness для дальнейшей работы

## Что Считать Успешным Результатом

Минимально успешная проверка:

- `--help` работает
- smoke test проходит
- guided mode стартует и не скрывает статус run
- raw CLI fallback работает
- stage plan виден до начала обработки
- warnings, checkpoints и финальные пути к артефактам остаются видимыми
- canonical JSON создаётся всегда

Хорошая проверка:

- дополнительно пройден хотя бы один realistic long-form run
- проверен хотя бы один guided run и один raw CLI run
- проверено поведение при `skipped` и `degraded` optional stages

## Шаблон Для Фиксации Результата

```text
Файл:
Команда:
Режим: guided / raw
Окружение: CPU / CUDA
First-run download: да / нет
Итог: success / fail
Stage plan виден: да / нет
Counters видны: да / нет
JSON создан: да / нет
TXT создан: да / нет
MD создан: да / нет
Checkpoint создан: да / нет
Alignment: completed / skipped / degraded
Diarization: completed / skipped / degraded
Warnings:
Наблюдения по качеству:
```
