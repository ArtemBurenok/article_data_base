import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton,QFileDialog,QMessageBox
import pandas as pd
from PyQt6 import QtWidgets
from sqlalchemy import create_engine
import datetime
from dbsettings import database_parametres
from interface_updated import Ui_MainWindow
from xml_parser.parser_article import parse_articles_to_excel
from xml_parser.parser_authors import extract_authors_info
from xml_parser.parser_unique_organizations import parse_affilations_to_excel
import psycopg2


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.widget_onlyicons.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.home_button_iconexpandedwidget.setChecked(True)
        self.import_button_onlyiconwidget = self.findChild(QPushButton, "import_button_onlyiconwidget")
        self.import_button_onlyiconwidget.clicked.connect(self.importButtonClickHandler)
        self.export_button = self.findChild(QPushButton, "pushButton")
        self.export_button.clicked.connect(self.process_data)
        self.import_button_expandedwidget = self.findChild(QPushButton, "import_button_expandedwidget")
        self.import_button_expandedwidget.clicked.connect(self.importButtonClickHandler)
        self.search_button = self.findChild(QPushButton, "Primary")
        self.search_button.clicked.connect(self.get_text)
        self.user_button = self.findChild(QPushButton, "user_button")
        self.user_button.clicked.connect(lambda: self.authorsReferenceToSQL(database_parametres))

    def process_data(self):
        connection = psycopg2.connect(
            dbname=database_parametres['dbname'],
            user=database_parametres['user'],
            password=database_parametres['password'],
            host=database_parametres['host'],
            port=database_parametres['port']
        )

        cursor = connection.cursor()

        sql_query = """
          SELECT DISTINCT
            article.item_id,
            article.doi,
            article.year,
            article.title_article,
            article.publisher,
            article.type,
            article.risc,
            article.issn,
            article.edn,
            article_author.author_id,
			CASE
  			WHEN article_author.author_name ~ '[A-Za-z]' THEN authors_reference_with_id.lastname
  			ELSE article_author.author_name
			END AS last_name,
            authors_organisations.org_id,
            authors_organisations.org_name,
            CASE
  			WHEN authors_splitted.first_name LIKE '%.%' THEN authors_reference_with_id.first_name
  			ELSE authors_splitted.first_name
			END AS first_name,
			CASE
  			WHEN authors_splitted.patronymic LIKE '%.%' OR authors_splitted.patronymic IS NULL THEN authors_reference_with_id.patronymic
  			ELSE authors_splitted.patronymic
			END,
			authors_reference_with_id.position,
			authors_reference_with_id.academic_degree,
			authors_reference_with_id.employment_relationship,
			authors_reference_with_id.birth_year,
            nested_auth.author_count,
			nested_aff.aff_count
        FROM
            authors_splitted
        JOIN
            authors_organisations  ON CAST(authors_splitted.author_id AS text) = authors_organisations.author_id
			AND authors_splitted.lastname = authors_organisations.author_name
        JOIN
            article_author  ON CAST(article_author.author_id AS text)  = authors_organisations.author_id
			AND authors_organisations.author_name = article_author.author_name
        JOIN
            article  ON article.item_id = article_author.item_id
		LEFT JOIN
			authors_reference_with_id  ON CAST(authors_reference_with_id.author_id AS text) = authors_organisations.author_id
        JOIN
            (
                SELECT item_id, COUNT(author_name) AS author_count
                FROM article_author
                GROUP BY item_id
            ) AS nested_auth ON article.item_id = nested_auth.item_id
		JOIN
			(
				SELECT article.item_id,COUNT(author_name) AS aff_count
				FROM article
				INNER JOIN article_author ON article.item_id = article_author.item_id
				GROUP BY doi,article.item_id
			)AS nested_aff ON article.item_id = nested_aff.item_id
        WHERE
            authors_organisations.org_id = '570'
                """

        cursor.execute(sql_query)
        result = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=columns)

        cursor.close()
        connection.close()

        excel_template_path = "../article_data_base/shablon_kbpr.xlsx"
        df_template = pd.read_excel(excel_template_path)

        df_template['Идентификатор DOI *'] = df['doi']
        df_template['Количество авторов *'] = df['author_count']
        df_template['Фамилия *'] = df['last_name']
        df_template['Имя *'] = df['first_name']
        df_template['Отчество'] = df['patronymic']
        df_template['Должность *'] = df['position']
        df_template['Ученая степень *'] = df['academic_degree']
        df_template['Тип трудовых отношений *'] = df['employment_relationship']
        df_template['Год рождения *'] = df['birth_year']
        df_template['Количество аффиляций *'] = df['aff_count']
        df_template['Аффиляция *'] = df['org_name']
        df_template['Дата публикации *'] = pd.to_datetime(df['year'], format='%Y').dt.strftime('01/01/%Y')
        df_template['Наименование публикации *'] = df['title_article']
        df_template['Наименование издания *'] = df['publisher']
        df_template['Вид издания  *'] = df['type']
        df_template['Идентификатор РИНЦ'] = df['risc']
        df_template['Идентификатор ISSN'] = df['issn']
        df_template['Идентификатор EDN'] = df['edn']

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = f"shablon_kbpr_{timestamp}.xlsx"
        df_template.to_excel(output_path)
        QMessageBox.information(self, "Экспорт", "Excel файл по шаблону кбпр создан!")

    def split_initials(self):
        query = """
        DROP TABLE IF EXISTS authors_splitted;
        CREATE TABLE  authors_splitted AS
        SELECT author_id, lastname,
            CASE
                WHEN initials LIKE '% %' THEN split_part(authors.initials, ' ', 1)
                WHEN initials NOT LIKE '% %' AND initials NOT LIKE '%.%' THEN initials
                WHEN initials LIKE '%.%' AND LENGTH(initials) = 2 THEN initials
                WHEN initials LIKE '%.%' AND LENGTH(initials) = 4 THEN LEFT(initials, 2)
				WHEN initials LIKE '%.%' AND LENGTH(initials) = 5 THEN LEFT(initials, 2)
                ELSE initials
            END AS first_name,
            CASE
                WHEN initials LIKE '% %' THEN split_part(authors.initials, ' ', -1)
                WHEN initials NOT LIKE '% %' AND initials NOT LIKE '%.%' THEN NULL
                WHEN initials LIKE '%.%' AND LENGTH(initials) = 2 THEN NULL
                WHEN initials LIKE '%.%' AND LENGTH(initials) = 4 THEN RIGHT(initials, 2)
				WHEN initials LIKE '%.%' AND LENGTH(initials) = 5 THEN RIGHT(initials, 3)
                ELSE initials
            END AS patronymic
        FROM authors
        """

        conn = psycopg2.connect(
            dbname=database_parametres['dbname'],
            user=database_parametres['user'],
            password=database_parametres['password'],
            host=database_parametres['host'],
            port=database_parametres['port']
        )
        cur = conn.cursor()

        cur.execute(query)

        conn.commit()

        cur.close()
        conn.close()

    def create_authors_reference(self):
        query = """
        DROP TABLE IF EXISTS authors_reference_with_id;
        CREATE TABLE authors_reference_with_id AS
        SELECT author_id,ar."Автор публикации" AS publication_author,at.lastname,at.first_name,at.patronymic,
        ar."Должность автора статьи в организ" AS position,
        ar."Ученая степень" AS academic_degree ,ar."Тип трудовых отношений" AS employment_relationship,ar."Год рождения автора" AS birth_year
        FROM authors_splitted AS at
	    INNER JOIN authors_reference AS ar
	    ON (at.lastname,at.first_name,at.patronymic) = (ar."Фамилия",ar."имя",ar."отчество")
        WHERE author_id IS NOT NULL
        UNION
        SELECT at.author_id,at.full_name,ar."Фамилия",ar."имя",ar."отчество",ar."Должность автора статьи в организ",
        ar."Ученая степень",ar."Тип трудовых отношений",ar."Год рождения автора"
        FROM (SELECT lastname || ' ' || initials as full_name,author_id FROM authors
        WHERE initials LIKE '%.%' AND LENGTH(initials)  = 4 AND author_id IS NOT NULL) AS at
	    INNER JOIN authors_reference AS ar
	    ON (at.full_name) = (ar."Автор публикации")
        WHERE author_id IS NOT NULL
        """

        conn = psycopg2.connect(
            dbname=database_parametres['dbname'],
            user=database_parametres['user'],
            password=database_parametres['password'],
            host=database_parametres['host'],
            port=database_parametres['port']
        )
        cur = conn.cursor()

        cur.execute(query)

        conn.commit()

        cur.close()
        conn.close()

    def import_xlsx_to_postgresql(self, database_params, xlsx_file_path, table_name,index_col,article):
        connection_str = f"postgresql://{database_params['user']}:{database_params['password']}@{database_params['host']}:{database_params['port']}/{database_params['dbname']}"
        engine = create_engine(connection_str)
        data_frame = pd.read_excel(xlsx_file_path,index_col=index_col)
        existing_data_query = f"SELECT * FROM {table_name}"
        existing_data = pd.read_sql(existing_data_query, engine)
        if article:
            existing_data['volume'] = data_frame['volume'].astype(object)
            existing_data['quartile'] = data_frame['quartile'].astype(object)
            existing_data['rcsi'] = data_frame['rcsi'].astype(object)
        merged_data = existing_data.merge(data_frame, how='outer').drop_duplicates(keep=False)
        merged_data.to_sql(table_name, engine, index=False, if_exists='replace')


    def importButtonClickHandler(self):
        fname = QFileDialog.getOpenFileName(self, "Open XML file", "", "All Files (*);; XML Files (*.xml)")
        if fname[0]:
            parse_articles_to_excel(fname[0])
            parse_affilations_to_excel(fname[0])
            extract_authors_info(fname[0])
            self.import_xlsx_to_postgresql(database_parametres, 'article_author.xlsx', 'article_author',0,False)
            self.import_xlsx_to_postgresql(database_parametres, 'article.xlsx', 'article',None,True)
            self.import_xlsx_to_postgresql(database_parametres, 'authors.xlsx', 'authors', 0, False)
            self.import_xlsx_to_postgresql(database_parametres, 'new_one_authors_organisations.xlsx', 'authors_organisations',None,False)
            self.import_xlsx_to_postgresql(database_parametres, 'one_unique_organisations.xlsx', 'organisations',0,False)
            self.split_initials()
            self.create_authors_reference()
            QMessageBox.information(self, "Успешный импорт", "Данные были перенесены в Базу Данных!")
        else:
            print("Выбор файла отменен. Файл не был перемещен.")

    # def import_xlsx_to_postgresql(self, database_params, xlsx_file_path, table_name):
    #     print(1)
    #     connection_str = f"postgresql://{database_params['user']}:{database_params['password']}@{database_params['host']}:{database_params['port']}/{database_params['dbname']}"
    #     print(2)
    #     engine = create_engine(connection_str)
    #     print(3)
    #     data_frame = pd.read_excel(xlsx_file_path)
    #
    #     data_frame.to_sql(table_name, engine, index=False, if_exists='replace')

    def searchButtonDBConnector(self, year, lastname):
        query = """
                        SELECT a.item_id, aa.author_name, a.linkurl, a.genre, a.type, a.journal_title, a.publisher, a.title_article
                        FROM article AS a
                        INNER JOIN article_author AS aa ON aa.item_id = a.item_id
                        WHERE a.year = '{year}' AND aa.author_name = '{lastname}'
                        """

        query = query.format(year=year, lastname=lastname)
        conn = psycopg2.connect(database="praktika", user="postgres", password="sword9999", host="localhost",
                                port="5432")
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
        self.ui.tableWidget.setRowCount(0)

        for row_number, row_data in enumerate(result):
            self.ui.tableWidget.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.ui.tableWidget.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))
        cur.close()
        conn.close()

    def get_text(self):
        text = self.ui.textEdit.toPlainText().strip()
        selected_text = self.ui.comboBox.currentText()
        self.searchButtonDBConnector(selected_text, text)

    def authorsReferenceToSQL(self,database_params):
        fname = QFileDialog.getOpenFileName(self, "Open XML file", "", "All Files (*);; XML Files (*.xml)")
        if fname[0]:
            connection_str = f"postgresql://{database_params['user']}:{database_params['password']}@{database_params['host']}:{database_params['port']}/{database_params['dbname']}"
            engine = create_engine(connection_str)
            data_frame = pd.read_excel(fname[0])
            data_frame.to_sql('authors_reference', engine, index=False, if_exists='replace')
            QMessageBox.information(self, "Успешный импорт", "Данные были перенесены в Базу Данных!")
        else:
            print("Выбор файла отменен. Файл не был перемещен.")

    def on_home_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def on_home_button_iconexpandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def on_articleDB_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)


    def on_articleDB_button_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def on_article_authorDB_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def on_article_authorDB_button_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def on_authorsDB_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    def on_authorsDB_button_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    def on_authors_organisationsDB_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(4)

    def on_authors_organisationsDB_button_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(4)

    def on_organisationsDB_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(5)

    def on_organisationsDB_button_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(5)

    def on_addingdatatoBD_button_iconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(6)

    def on_addingdatatoBD_button_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(6)

    def on_import_button_onlyiconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(6)

    def on_import_button_expandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(6)

    def on_export_button_onlyiconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(7)

    def on_export_button_expandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(7)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r") as style_file:
        style_str = style_file.read()
    app.setStyleSheet(style_str)


    window = MainWindow()
    window.show()

    sys.exit(app.exec())