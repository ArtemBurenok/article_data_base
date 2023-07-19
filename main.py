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
# from parser_article import parse_articles_to_excel
# from parser_authors import extract_authors_info
# from parser_unique_organizations import parse_affilations_to_excel
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
        self.search_button = self.findChild(QPushButton, "general_data_export_button")
        self.search_button.clicked.connect(self.get_test_auf)
        self.user_button = self.findChild(QPushButton, "user_button")
        self.user_button.clicked.connect(lambda: self.authorsReferenceToSQL(database_parametres))
        self.add_one_row_button = self.findChild(QPushButton, "add_one_row_button")
        self.add_one_row_button.clicked.connect(self.addOneRowToDB)

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
  			WHEN authors_splitted.lastname ~ '[A-Za-z]' AND authors_reference_with_id.birth_year IS NOT NULL  THEN authors_reference_with_id.lastname
  			ELSE authors_splitted.lastname
			END AS last_name,
            authors_organisations.org_id,
            authors_organisations.org_name,
            CASE
  			WHEN (authors_splitted.first_name LIKE '%.%' AND authors_reference_with_id.birth_year IS NOT NULL) OR (authors_splitted.first_name ~ '[A-Za-z]' AND authors_reference_with_id.birth_year IS NOT NULL) OR authors_splitted.first_name IS NULL 
			THEN authors_reference_with_id.first_name
  			ELSE authors_splitted.first_name
			END AS first_name,
			CASE
  			WHEN (authors_splitted.patronymic LIKE '%.%' AND authors_reference_with_id.birth_year IS NOT NULL) OR authors_splitted.patronymic IS NULL OR (authors_splitted.patronymic ~ '[A-Za-z]'  AND authors_reference_with_id.birth_year IS NOT NULL)
			THEN authors_reference_with_id.patronymic
  			ELSE authors_splitted.patronymic
			END AS patronymic,
			authors_reference_with_id.position,
			authors_reference_with_id.academic_degree,
			authors_reference_with_id.employment_relationship,
			authors_reference_with_id.birth_year,
            nested_auth.author_count
        FROM
            authors_splitted
        JOIN
            authors_organisations  ON CAST(authors_splitted.author_id AS text) = authors_organisations.author_id
			OR (authors_splitted.author_id IS NULL AND  authors_organisations.author_id IS NULL)
			AND authors_splitted.lastname = authors_organisations.author_name
        JOIN
            article_author  ON CAST(article_author.author_id AS text)  = authors_organisations.author_id
			OR (article_author.author_id IS NULL AND  authors_organisations.author_id IS NULL)
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
        # df_template['Количество аффиляций *'] = df['aff_count']
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


    def execute_query_with_params(self,query):
        query = query
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

    deleteUselessDuplicatesFromASSTable_query = """
            DELETE FROM authors_splitted
            WHERE author_id IN 
            (SELECT author_id
            FROM authors_splitted
            GROUP BY author_id
            HAVING COUNT(author_id) > 1)
            AND first_name LIKE '%.%' OR (initials NOT LIKE '% %' AND initials NOT LIKE '%.%')
            """

    getOnlyDistinctRowsFromAATable_query = """
            CREATE TABLE article_author_distinct AS
            SELECT DISTINCT * FROM article_author;
            DROP TABLE article_author;
            ALTER TABLE article_author_distinct 
            RENAME TO article_author;
            """

    setEmptyValuesToNullAOTable_query = """
            UPDATE authors_organisations
            SET author_id = NULL WHERE author_id = ' ';
            """
    setEmptyValuesToNullAATable_query = """
            UPDATE article_author
            SET author_id = NULL WHERE author_id IS NULL
            """
    setEmptyValuesToNullASSTable_query = """
            UPDATE authors_splitted
            SET author_id = NULL WHERE author_id IS NULL
            """
    splitInitials_query = """
        DROP TABLE IF EXISTS authors_splitted;
        CREATE TABLE  authors_splitted AS
        SELECT author_id, lastname,initials,
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
        FROM authors;
        """
    createAuthorsReference_query = """
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
    def import_xlsx_to_postgresql(self, database_params, xlsx_file_path, table_name,index_col,article):
        articleTableIsEmpty = False
        connection_str = f"postgresql://{database_params['user']}:{database_params['password']}@{database_params['host']}:{database_params['port']}/{database_params['dbname']}"
        engine = create_engine(connection_str)

        def replace_float_with_null(value):
            if isinstance(value, float):
                return pd.NA
            return value

        float_columns = [
            'linkurl',
            'genre',
            'type',
            'journal_title',
            'issn',
            'eissn',
            'publisher',
            'vak',
            'wos',
            'scopus',
            'number',
            'page_begin',
            'page_end',
            'language',
            'title_article',
            'doi',
            'edn',
            'risc',
            'corerisc',
            'volume']
        data_frame = pd.read_excel(xlsx_file_path,index_col=index_col)
        if table_name == 'article':
            for column in float_columns:
                data_frame[column] = data_frame[column].apply(lambda x: replace_float_with_null(x))
        existing_data_query = f"SELECT DISTINCT * FROM {table_name}"
        existing_data = pd.read_sql(existing_data_query, engine)
        if table_name == 'authors_organisations':
            data_frame.reset_index(drop=True, inplace=True)
            data_frame = data_frame.iloc[0:]
            data_frame['author_id'] = data_frame['author_id'].replace(' ', pd.NA)
        if table_name == 'article' and len(existing_data) == 0:
            articleTableIsEmpty = True
        if article and not articleTableIsEmpty:
            column_types = existing_data.dtypes
            column_types_excel = data_frame.dtypes
            # print(column_types)
            # print(column_types_excel)
            unequal_columns = column_types_excel[column_types_excel != column_types]
            # for column_name in unequal_columns.index:
            #     print(f"\nColumn '{column_name}' has different types:")
            #     print(f"existing_data: {column_types_excel[column_name]}")
            for column in unequal_columns.index:
                existing_data[column] = data_frame[column].astype(column_types_excel[column])
        rows_before = len(existing_data)
        if table_name == 'article_author':
            merged_data = existing_data.merge(data_frame, how='outer')
        else:
            merged_data = existing_data.merge(data_frame, how='outer').drop_duplicates(keep=False)
        # if table_name == 'article_author':
        #     column_types = existing_data.dtypes
        #     column_types_excel = data_frame.dtypes
        #     column_types_merged = merged_data.dtypes
        #     print(column_types)
        #     print(column_types_excel)
        #     print(column_types_merged)
        # #     pd.set_option('display.max_columns', None)
        # #     pd.set_option('display.max_rows', None)
        # #     print(existing_data.select_dtypes(include=['object']).applymap(type))
        # #     print(data_frame.select_dtypes(include=['object']).applymap(type))
        merged_data_with_duplicates = existing_data.merge(data_frame, how='outer')
        num_duplicates = len(merged_data_with_duplicates) - len(merged_data)
        rows_added = len(merged_data) - rows_before
        if rows_added >= 0:
            print(f"Added to {table_name}  {rows_added} rows")
        else:
            print(f"Deleted from {table_name} {rows_added} rows")
        print(f"Found {num_duplicates} in {table_name}")
        print('                                        ')
        merged_data.to_sql(table_name, engine, index=False, if_exists='replace')


    def importButtonClickHandler(self):
        self.ui.progressBar.setValue(0)
        fname = QFileDialog.getOpenFileName(self, "Open XML file", "", "All Files (*);; XML Files (*.xml)")
        if fname[0]:
            parse_articles_to_excel(fname[0])
            self.ui.progressBar.setValue(10)
            parse_affilations_to_excel(fname[0])
            self.ui.progressBar.setValue(20)
            extract_authors_info(fname[0])
            self.ui.progressBar.setValue(30)
            self.import_xlsx_to_postgresql(database_parametres, 'article_author.xlsx', 'article_author', 0, False)
            self.ui.progressBar.setValue(35)
            self.import_xlsx_to_postgresql(database_parametres, 'article.xlsx', 'article', None, True)
            self.ui.progressBar.setValue(40)
            self.import_xlsx_to_postgresql(database_parametres, 'authors.xlsx', 'authors', 0,False)
            self.ui.progressBar.setValue(45)
            self.import_xlsx_to_postgresql(database_parametres, 'new_one_authors_organisations.xlsx', 'authors_organisations', 0,False)
            self.ui.progressBar.setValue(50)
            self.import_xlsx_to_postgresql(database_parametres, 'one_unique_organisations.xlsx', 'organisations',0,False)
            self.ui.progressBar.setValue(55)
            self.execute_query_with_params(self.setEmptyValuesToNullAOTable_query)
            self.ui.progressBar.setValue(60)
            self.execute_query_with_params(self.setEmptyValuesToNullAATable_query)
            self.ui.progressBar.setValue(70)
            self.execute_query_with_params(self.splitInitials_query)
            self.ui.progressBar.setValue(75)
            self.execute_query_with_params(self.deleteUselessDuplicatesFromASSTable_query)
            self.ui.progressBar.setValue(80)
            self.execute_query_with_params(self.setEmptyValuesToNullASSTable_query)
            self.ui.progressBar.setValue(90)
            self.execute_query_with_params(self.createAuthorsReference_query)
            self.ui.progressBar.setValue(95)
            self.execute_query_with_params(self.getOnlyDistinctRowsFromAATable_query)
            self.ui.progressBar.setValue(100)
            QMessageBox.information(self, "Успешный импорт", "Данные были перенесены в Базу Данных!")
        else:
            print("Выбор файла отменен. Файл не был перемещен.")

    # def import_xlsx_to_postgresql(self, database_params, xlsx_file_path, table_name):
    #     connection_str = f"postgresql://{database_params['user']}:{database_params['password']}@{database_params['host']}:{database_params['port']}/{database_params['dbname']}"
    #     engine = create_engine(connection_str)
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
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
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

    def userChoicePatternFetchFromDB(self,columns):
        query = """
                        SELECT DISTINCT {columns}
        FROM authors_splitted
        JOIN authors_organisations ON CAST(authors_splitted.author_id AS text) = authors_organisations.author_id
                                   OR (authors_splitted.author_id IS NULL AND authors_organisations.author_id IS NULL)
                                   AND authors_splitted.lastname = authors_organisations.author_name
        JOIN article_author ON CAST(article_author.author_id AS text) = authors_organisations.author_id
                            OR (article_author.author_id IS NULL AND authors_organisations.author_id IS NULL)
                            AND authors_organisations.author_name = article_author.author_name
        JOIN article ON article.item_id = article_author.item_id
        LEFT JOIN authors_reference_with_id ON CAST(authors_reference_with_id.author_id AS text) = authors_organisations.author_id
        JOIN (
            SELECT item_id, COUNT(author_name) AS author_count
            FROM article_author
            GROUP BY item_id
        ) AS nested_auth ON article.item_id = nested_auth.item_id
        JOIN (
            SELECT article.item_id, COUNT(author_name) AS aff_count
            FROM article
            INNER JOIN article_author ON article.item_id = article_author.item_id
            GROUP BY doi, article.item_id
        ) AS nested_aff ON article.item_id = nested_aff.item_id
        WHERE authors_organisations.org_id = '570'
                           """
        query = query.format(columns=columns)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
        columns = columns.split(",")
        df = pd.DataFrame(result, columns=columns)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = f"userTemplate_{timestamp}.xlsx"
        df.to_excel(output_path, index=False, sheet_name='Sheet1')
        QMessageBox.information(self, "Экспорт", "Excel файл по шаблону пользователя создан!")

    def exportConnector(self, year, lastname):
        query = """
                        SELECT a.item_id, aa.author_name, a.linkurl, a.genre, a.type, a.journal_title, a.publisher, a.title_article
                        FROM article AS a
                        INNER JOIN article_author AS aa ON aa.item_id = a.item_id
                        WHERE a.year = '{year}' AND aa.author_name = '{lastname}'
                        """

        query = query.format(year=year, lastname=lastname)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()

    def get_test_auf(self):
        text_array = []

        for combobox in self.ui.comboboxes:
            current_text = combobox.currentText()
            if current_text != 'None':
                if current_text in ["item_id", "linkurl", "genre", "type", "journal_title", "issn", "eissn",
                                    "publisher", "vak", "rcsi", "wos", "scopus", "quartile", "year", "number",
                                    "contnumber", "volume", "page_begin", "page_end", "language",
                                    "title_article", "doi", "edn", "grnti", "risc", "corerisc"]:
                    text_array.append("article." + current_text)
                elif current_text == "last_name":
                    text_array.append(
                        "CASE WHEN authors_splitted.lastname ~ '[A-Za-z]' AND authors_reference_with_id.birth_year IS NOT NULL THEN authors_reference_with_id.lastname ELSE authors_splitted.lastname END AS last_name")
                elif current_text == "first_name":
                    text_array.append(
                        "CASE WHEN (authors_splitted.first_name LIKE '%.%' AND authors_reference_with_id.birth_year IS NOT NULL) OR (authors_splitted.first_name ~ '[A-Za-z]' AND authors_reference_with_id.birth_year IS NOT NULL) OR authors_splitted.first_name IS NULL THEN authors_reference_with_id.first_name ELSE authors_splitted.first_name END AS first_name")
                elif current_text == "patronymic":
                    text_array.append(
                        "CASE WHEN (authors_splitted.patronymic LIKE '%.%' AND authors_reference_with_id.birth_year IS NOT NULL) OR authors_splitted.patronymic IS NULL OR (authors_splitted.patronymic ~ '[A-Za-z]'  AND authors_reference_with_id.birth_year IS NOT NULL) THEN authors_reference_with_id.patronymic ELSE authors_splitted.patronymic END AS patronymic")
                elif current_text in ["position", "degree", "employment_relationship",
                        "birth_year"]:
                    text_array.append("authors_reference_with_id." + current_text)
                elif current_text == "author_count":
                    text_array.append("nested_auth." + current_text)
                elif current_text == "aff_count":
                    text_array.append("nested_aff." + current_text)
                elif current_text == "org_id":
                    text_array.append("authors_organisations." + current_text)
                elif current_text == "org_name":
                    text_array.append("authors_organisations." + current_text)
                else:
                    text_array.append(current_text)
        result = ','.join(text_array)
        print(result)
        result = result.split(",")
        print(result)
        result = pd.Series(result).drop_duplicates().tolist()
        print(result)
        result = ','.join(result)
        print(result)
        self.userChoicePatternFetchFromDB(result)

    def get_text(self):
        text = self.ui.textEdit.toPlainText().strip()
        selected_text = self.ui.comboBox.currentText()
        self.searchButtonDBConnector(selected_text, text)

    def addOneRowToDB(self):
        for row in range(self.ui.tableWidget_add_row.rowCount()):
            row_data = []
            for column in range(self.ui.tableWidget_add_row.columnCount()):
                item = self.ui.tableWidget_add_row.item(row, column)
                if item is not None:
                    cell_data = item.text()
                    row_data.append(cell_data)
                else:
                    row_data.append("NULL")
            newRowForArticleTable = ', '.join(row_data[:26]) # article
            newRowForAuthorSplittedTable = ', '.join([row_data[26],row_data[27],row_data[28],row_data[29],row_data[39]])  # auth_splitted
            newRowForArticleAuthorTable = ', '.join([row_data[0], row_data[26], row_data[27]]) # article_author
            newRowForAuthorsOrganisationsTable = ', '.join([row_data[26], row_data[27], row_data[37], row_data[38]]) #auth_org
            newRowForOrganisationsTable = ', '.join([row_data[37], row_data[38]])  # organisations
            newRowForAuthorsReferenceWithIDTable = ', '.join([row_data[26], row_data[30], row_data[27], row_data[28], row_data[29], row_data[31]
            , row_data[32], row_data[33], row_data[34]]) # auth_ref_with_id
            print(newRowForAuthorSplittedTable)
            self.insertNewRowInArticleTable(newRowForArticleTable)
            self.insertNewRowInAuthorsSplittedTable(newRowForAuthorSplittedTable)
            self.insertNewRowInArticleAuthorTable(newRowForArticleAuthorTable)
            self.insertNewRowInAuthorsOrganisationsTable(newRowForAuthorsOrganisationsTable)
            self.insertNewRowInOrganisationsTable(newRowForOrganisationsTable)
            self.insertNewRowInAuthorsReferenceTable(newRowForAuthorsReferenceWithIDTable)
            QMessageBox.information(self, "Успешно", "Строка была добавлена в базу данных!")

    def insertNewRowInArticleTable(self, row_1):
        query = """
                        INSERT INTO article VALUES
                        ({});
                        """

        query = query.format(row_1)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

    def insertNewRowInAuthorsSplittedTable(self, row_1):
        query = """
                        INSERT INTO authors_splitted VALUES
                        ({});
                        """

        query = query.format(row_1)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

    def insertNewRowInArticleAuthorTable(self, row_1):
        query = """
                        INSERT INTO article_author VALUES
                        ({});  
                        """

        query = query.format(row_1)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

    def insertNewRowInAuthorsOrganisationsTable(self, row_1):
        query = """
                        INSERT INTO authors_organisations VALUES
                        ({}); 
                        """

        query = query.format(row_1)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

    def insertNewRowInOrganisationsTable(self, row_1):
        query = """
                        INSERT INTO organisations VALUES
                        ({}); 
                        """

        query = query.format(row_1)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

    def insertNewRowInAuthorsReferenceTable(self, row_1):
        query = """
                        INSERT INTO authors_reference_with_id VALUES
                        ({});  
                        """

        query = query.format(row_1)
        conn = psycopg2.connect(database=database_parametres['dbname'],
                                user=database_parametres['user'],
                                password=database_parametres['password'],
                                host=database_parametres['host'],
                                port=database_parametres['port'])
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
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

    def on_export_button_onlyiconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(7)

    def on_export_button_expandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(7)

    def on_import_button_onlyiconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(9)

    def on_import_button_expandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(9)

    def on_pushButton_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(8)

    def on_pushButton_5_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(8)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r") as style_file:
        style_str = style_file.read()
    app.setStyleSheet(style_str)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())