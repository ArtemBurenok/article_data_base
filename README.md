# article_data_base
<h1 align="center">Описание</h1>

* Title – название журнала
  
* Issn – идентификатор

* Publisher – организация, которая выпускает журнал.
  
В теге journal должены быть обязательно vak, rsci, wos, scopus. Кроме того, нужно завести поле квартили.

Проверка на квартили (загружает сторонние данные и если года совпадают, то присваивают квартиль, который из загруженных данных).

* Issn, eissn – уникальны для каждого журнала.
  
* Pages - начало и конец статьи, нужно создать два столбца – страница начала статьи и страница конца статьи (пример (5-6) начало и конец, может быть одна страница.).
  
Вообще говоря, нужно заводить любые поля, которые не встречались, потом можно удалить. 

* Title - название статьи, могут встречаться служебные знаки CO<sub>2</sub>.
  
Авторов может быть много, статья одна.

* Doi – международный идентификатор (может не быть)
* AuthorId – уникальный код автора (Фамилию в столбец фамилия, имя и отчество в столбец имя)
  
У автора 3 поля:  Фамилия, имя, id

* Аффиляции загрузить все (имя организации, id организации)

Автор может быть на русском и на английском, id один и тот же.

Пока храним записи по item_id.

Абстракты, ключевые слова, ссылки не храним.

<h1 align="center">Основные задачи</h1>

1) Возможность загрузить данные, при этом проверяя новые записи на наличие в базе данных.

2) Если есть похожие записи в старых и новых данных (id совпадают), то выводится диалоговое окно (сравнить поля и показать различия).
   
3) Выгрузка данных (уточнить поддерживает ли xlsx, csv).
   
4) Выгрузка по запросу (например по году) (выгружается xlsx).
   
5) Возможность завести новые поля.
   
6) По дефолту выгружать поля, помеченные в excel файле шаблонкбпр.xlsx, но Я думаю, что нужно добавить интерфейс для выгрузки дополнительных полей.

**Замечание**: выгружать, только тех авторов, у которых в аффиляциях есть ИПНГ РАН.
