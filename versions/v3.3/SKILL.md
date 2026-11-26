---
name: form-skills
description: Проектиране на физически предмети отвътре навън, с размерни модели, проверка, итерации и архив. Версия 3.3, кандидат.
---
# FORM SKILLS v3.3 — candidate
Приложи методиката като работа, не като преразказ. Прочети reference-v3.3.md за пълните девет умения и историческите източници. Това е независима процедура, не официална методика на Apple или Джонатан Айв. Историческите източници не са повторно проверени в тази версия.

## Работен ред
1. Заключи неизменните изисквания. Питай само ако липсва незаменима информация; иначе обозначи допусканията. Не наследявай размери от примери или стари версии при нов проект.
2. Компоновка (13): опиши всички обеми с три размера, координати, монтажни резерви, пътища за монтаж и обслужване. Построй три подредби; изведи трите габарита на всяка със сметки. Провери пресичанията и свободните пътища, не само общия обем.
3. Маса (1): три габарита, две отношения, водещ жест в едно изречение. Изведи ограниченията от ръката или мястото; не представяй предполагаем хват като измерен. При променлива дебелина дай минимум и максимум, включително издадени части.
4. Материал и процес (4): основен материал и процес, три лесни и три невъзможни за него операции; функционалните изключения се назовават. Всяка линия има конструктивна причина.
5. Ръб (2): преди фронталния изглед построи сечение 10:1 със стени, легла, сглобки и размерни вериги. Дай допирателни в двата края; не наричай G1 преход G2 без доказателство. Провери план, сечение и пространствени ъгли.
6. Части и шевове (5): част и нейният шев са едно събитие; отвори, бутони, обективи, светещи зони, кабел и основа се броят отделно. Индивидуален списък, общ брой, какво се губи при следваща редукция. Съгласувай списъка с чертежа.
7. Сглобки (6): всяка среща има процеп g, стъпало, допуск ±d и 100*d/g процента; при мек материал опиши прибиране на ръба. Провери крайни стойности и натрупване; не измисляй производствени гаранции.
8. Светлина (3): покритие за всяка повърхност, една целенасочена линия на отражение и причина за нея.
9. Модели (10): въпрос преди модела, отговор след него. Три варианта на едно решение с един променен параметър, в еднакъв мащаб; отделно могат да се сравнят различни жестове. Сравни с познат предмет при надеждни размери. Построй SVG или параметричен модел от един източник на числа. Провери размерите, координатите, пресичанията, изгледите и сеченията. При несъответствие поправи и покажи преди/след. Не замествай чертеж с рендер.
10. Преценка (11): най-силно възражение преди представяне, най-добър отхвърлен вариант и причина. Опиши действителния силует. Ако не съвпада с жеста, върни се към маса или ръб; не преименувай грешката на успех. При промяна на заданието започни от компоновката и преначертай целия предмет. Обосновката е накрая.

## Изпълнима проверка
За ротационни тела построй и измери профила с оригиналния profile_check.py и приложи изхода му.
Команда: python3 profile_check.py spec.json out.png
Вход: nodes [[r,z,angle],...] от върха към основата (0 навън, 90 надолу, 180 навътре), или points [[r,z],...] със стъпка най-много 0.1 mm. Винаги declared {height_mm,diameter_mm}, keepouts [{name,z0,z1,r}], wall в mm. Не променяй скрипта. Приложи пълния stdout и PNG за всяка итерация. При разминаване, ръб, гърло или непобиране поправи и изпълни отново; запази и неуспешните изходи. Провери отделно z граници, действителни 3D обеми и монтаж. За неротационни тела използвай числени проверки на координати, размерни вериги и сечения; не прилагай скрипта насила. Ако кодът не може да се изпълни, кажи го, приложи неизпълнен код и не фабрикувай изход.

## Десет условия за приемане (задължителна финална таблица)
За всяко: изпълнено / частично / не, с конкретно доказателство или липса.
1. Всеки габарит е изведен от вътрешностите и ръката/мястото.
2. Сеченията показват стените и срещите и се сумират до общия размер.
3. Допирателните са зададени и проверени; отвесен край под плоча е гърло.
4. Индивидуално броене по единно правило.
5. Всяка нова част/шев има ново броене и сечение.
6. Допуск и процент; меките материали имат описано прибиране.
7. Чертеж от числа, съгласуван с модела.
8. Описан и проверен силует, съвпадащ с водещия жест.
9. След промяна — нова компоновка, чертеж и отношения за цялото.
10. Всички пропуски са назовани, без самооценка с точки.
Проектът е приет по методиката само ако всички приложими условия са изпълнени; физическата и производствената валидация са отделни. Не твърди, че екранен модел проверява хват, тегло, акустика, топлина или безопасност.

## Ново във v3.2: рендер и архив
След обширен проект създай продуктов рендер преди ZIP, освен ако текущото задание забранява изображения. Рендерът е визуализация, не доказателство. Сравни го с размерния модел: силует, камери, бутони, шевове, отвори, материали. При несъответствие опитай корекция или маркирай като отхвърлена визуализация; не я представяй за точна. Не променяй числата заради свободно генерирана картина.
Архивирай пълния текст (ако е наличен; иначе обозначи резюме), спецификации, код, SVG, изходи, всички итерации, рендер и финална таблица. Добави README с версия, допускания, авторитетен геометричен файл и известни несъответствия. Провери действителното съществуване на файловете и целостта на ZIP преди линк. Не измисляй файлове, проверки или резултати. Ако инструмент липсва, назови ограничението. Приоритет има конкретното задание на потребителя.

## v3.3 evidence gates (candidate; not published)

These gates extend rather than replace the original methodology.

1. **Single geometry authority.** A machine-readable manifest owns dimensions, axes, units, design version and the status of each dimension (supplied constraint / calculated / assumption). Images cannot alter the manifest. Label an inconsistent visual prototype rejected.
2. **Axis discipline.** For non-axisymmetric objects use an explicit coordinate frame. For cars use length, width, height and ratios H/W, W/L; never silently treat length as thickness.
3. **Traceable surface continuity.** A visually smooth shaded section is not measured G2. Only label a junction G2 when a parametric surface/curve proves common position, tangent and curvature to a specified tolerance. Otherwise mark unverified. Before/after sections must use the same section plane and scale.
4. **Two counting ledgers.** Count physical items/seams/openings independently from visual gestures. Stable IDs, category, view and before/after state are mandatory. No percentage without individually reconciled evidence.
5. **Manufacturing and tolerance.** State tool access, material, forming limits, assembly and repair access, and nominal clearance stack. Prototype values remain assumptions until process capability and stacks are verified.
6. **Cross-view audit.** Check profile, front, rear, three-quarter, and one close detail against the same parameterized geometry. If a view is missing, label UNKNOWN. Do not call a generated concept board a CAD test.
7. **Rejection loop.** Before each iteration state the question and changed parameter. After it, record result, strongest objection, rejected alternative and exactly what was corrected. A change must not silently rewrite locked constraints.
8. **Acceptance evidence.** Each of the existing ten conditions has PASS / FAIL / UNKNOWN and a specific artifact. An attractive render and a self-rated checklist never establish independent validation.

Deliver the manifest, before/after geometry and edge sections, two count ledgers, checker inputs and outputs, view audit, assumptions, test log and rejected variants. Preserve failures. Present a product render before a ZIP only when tooling permits; both are deliverables, not dimensional proof. Verify generated files before linking. No publication without owner approval.
