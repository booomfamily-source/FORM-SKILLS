# FORM SKILLS v3.4 candidate

Предложение за надграждане на v3.2 и на кандидата v3.3. Не е публикувано и не променя LATEST.

Прочети SKILL.md, reference-v3.4.md и TEST_RESULTS.md.

    python3 regression_test.py
    python3 project_check.py examples/form04-manifest.json
    python3 section_check.py examples/form04-edge.json out.png
    python3 profile_check.py examples/speaker-fixed.json out.png

Нужни са Python 3 и matplotlib (само за чертежите).

Всички размери в примерите са допускания. Скриптовете проверяват една крива, едно сечение и съгласуваността на манифеста; не проверяват CAD, производство, хват или безопасност.
