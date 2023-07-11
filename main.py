import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton,QFileDialog,QMessageBox
import pandas as pd
from sqlalchemy import create_engine
import datetime
from dbsettings import database_parametres
from design import Ui_MainWindow
from xml_parser.parser_authors import extract_authors_info
from xml_parser.parser_affilations import parse_affilations_to_excel
from xml_parser.parser_article import parse_articles_to_excel


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

    def process_data(self):
        db_params = {
            'dbname': "test_db",
            'user': "postgres",
            'password': "1234",
            'host': "localhost",
            'port': "5432"
        }

        connection_url = f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}"

        engine = create_engine(connection_url)

        sql_query = """
         SELECT DISTINCT
            a.item_id,
            a.doi,
            a.year,
            a.title_article,
            a.publisher,
            a.type,
            a.risc,
            a.issn,
            a.edn,
            aa.author_id,
            aa.author_name,
            ao.org_id,
            ao.org_name,
            au.initials,
            nested.author_count
        FROM
            authors AS au
        JOIN
            authors_organisations AS ao ON CAST(au.author_id AS text) = ao.author_id
			AND au.lastname = ao.author_name
        JOIN
            article_author AS aa ON CAST(aa.author_id AS text)  = ao.author_id
			AND ao.author_name = aa.author_name
        JOIN
            article AS a ON a.item_id = aa.item_id
        JOIN
            (
                SELECT item_id, COUNT(author_name) AS author_count
                FROM article_author
                GROUP BY item_id
            ) AS nested ON a.item_id = nested.item_id
        WHERE
            ao.org_id = '570';
        """

        df = pd.read_sql_query(sql_query, engine)

        excel_template_path = "../article_data_base/shablon_kbpr.xlsx"
        df_template = pd.read_excel(excel_template_path)

        df_template['Идентификатор DOI *'] = df['doi']
        df_template['Количество авторов *'] = df['author_count']
        df_template['Фамилия *'] = df['author_name']
        df_template['Имя *'] = df['initials']
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


    def import_xlsx_to_postgresql(self,database_params, xlsx_file_path, table_name):
        connection_str = f"postgresql://{database_params['user']}:{database_params['password']}@{database_params['host']}:{database_params['port']}/{database_params['dbname']}"
        engine = create_engine(connection_str)

        data_frame = pd.read_excel(xlsx_file_path)

        data_frame.to_sql(table_name, engine, index=False, if_exists='replace')



    def importButtonClickHandler(self):
        fname = QFileDialog.getOpenFileName(self, "Open XML file", "", "All Files (*);; XML Files (*.xml)")

        if fname[0]:
            extract_authors_info(fname[0])
            parse_articles_to_excel(fname[0])
            parse_affilations_to_excel(fname[0])
            self.import_xlsx_to_postgresql(database_parametres, 'article_author.xlsx', 'article_author')
            self.import_xlsx_to_postgresql(database_parametres, 'article.xlsx', 'article')
            self.import_xlsx_to_postgresql(database_parametres, 'authors.xlsx', 'authors')
            self.import_xlsx_to_postgresql(database_parametres, 'authors_organisations.xlsx', 'authors_organisations')
            self.import_xlsx_to_postgresql(database_parametres, 'organisations.xlsx', 'organisations')
            QMessageBox.information(self, "Успешный импорт", "Данные были перенесены в Базу Данных!")
        else:
            print("Выбор файла отменен. Файл не был перемещен.")

    def on_user_btn_clicked(self):
        self.ui.stackedWidget.setCurrentIndex(0)

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
        self.ui.stackedWidget.setCurrentIndex(7)

    def on_import_button_expandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(7)

    def on_export_button_onlyiconwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(8)

    def on_export_button_expandedwidget_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(8)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r") as style_file:
        style_str = style_file.read()
    app.setStyleSheet(style_str)


    window = MainWindow()
    window.show()

    sys.exit(app.exec())