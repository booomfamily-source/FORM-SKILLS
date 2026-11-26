# FORM SKILLS v3.5 — кандидат за преглед

База: каченият пакет v3.4, Git commit `9e3374566bbcaf3cc2cdd54edd944c69b3fa7d1b`, директория `versions/v3.4/`. Това е пакетът от PR #2, а не различният кандидат в `release/v3.4-verified-checker`. Предишните версии не са редактирани. LATEST не се променя.

Прочети SKILL.md, reference-v3.5.md, AUDIT_BG.md и TEST_RESULTS.md. Нужен е Python 3; matplotlib е нужен само за PNG.

```sh
python3 regression_test.py
python3 project_check.py examples/form04-manifest.json
python3 section_check.py examples/form04-edge.json out-section.png
python3 profile_check.py examples/speaker-fixed.json out-profile.png
```

Form 04 остава PROJECT_INCOMPLETE (код 1): няма проверен three_quarter изглед. Това не се променя, за да изглежда тестът успешен. Ротационният пример има добавени declared размери, изведени от собствената му крива, не от измерен предмет.

Прочитането на файловете не означава постоянна инсталация. За одобрение се разглежда този кандидат изрично; той не се активира чрез LATEST. Нови дизайн тестове в чиста сесия и физически/CAD проверки не са извършени.
