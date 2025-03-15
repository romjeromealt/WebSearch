import os
import csv
import hashlib

from constants import *

COMMON_LOCALE_SIGN = "★"
SKIPPED_DOMAIN_SUGGESTIONS_FILE_PATH = os.path.join(os.path.dirname(__file__), "skipped_domain_suggestions.txt")

class WebsiteLoader:
    CSV_DIR = os.path.join(os.path.dirname(__file__), "csv")

    locales = set()
    domains = set()
    include_global = False

    @staticmethod
    def get_csv_files():
        if not os.path.exists(WebsiteLoader.CSV_DIR):
            return []
        return [os.path.join(WebsiteLoader.CSV_DIR, f) for f in os.listdir(WebsiteLoader.CSV_DIR) if f.endswith(".csv")]

    @staticmethod
    def get_selected_csv_files(config_ini_manager):
        csv_files = WebsiteLoader.get_csv_files()
        selected_files = config_ini_manager.get_list("websearch.enabled_files", DEFAULT_ENABLED_FILES)
        return [file for file in csv_files if os.path.basename(file) in selected_files]

    @staticmethod
    def get_all_and_selected_files(config_ini_manager):
        all_files = [os.path.basename(f) for f in WebsiteLoader.get_csv_files()]
        selected_files = config_ini_manager.get_list("websearch.enabled_files", DEFAULT_ENABLED_FILES)
        return all_files, selected_files

    @staticmethod
    def generate_hash(string: str) -> str:
        return hashlib.sha256(string.encode()).hexdigest()[:16]

    @staticmethod
    def has_hash_in_file(hash_value: str, file_path) -> bool:
        if not os.path.exists(file_path):
            return False
        with open(file_path, "r", encoding="utf-8") as file:
            return hash_value in file.read().splitlines()

    @staticmethod
    def save_hash_to_file(hash_value: str, file_path):
        if not WebsiteLoader.has_hash_in_file(hash_value, file_path):
            with open(file_path, "a", encoding="utf-8") as file:
                file.write(hash_value + "\n")

    @staticmethod
    def load_skipped_domains() -> set:
        if not os.path.exists(SKIPPED_DOMAIN_SUGGESTIONS_FILE_PATH):
            return set()
        with open(SKIPPED_DOMAIN_SUGGESTIONS_FILE_PATH, "r", encoding="utf-8") as file:
            return {line.strip() for line in file if line.strip()}

    @staticmethod
    def save_skipped_domain(domain: str):
        with open(SKIPPED_DOMAIN_SUGGESTIONS_FILE_PATH, "a", encoding="utf-8") as file:
            file.write(domain + "\n")

    @classmethod
    def load_websites(cls, config_ini_manager):
        websites = []
        selected_csv_files = cls.get_selected_csv_files(config_ini_manager)

        for selected_file_path in selected_csv_files:
            if not os.path.exists(selected_file_path):
                continue

            locale = os.path.splitext(os.path.basename(selected_file_path))[0].replace("-links", "").upper()
            if locale == "COMMON":
                locale = COMMON_LOCALE_SIGN

            with open(selected_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

                for row in reader:
                    if not row:
                        continue

                    nav_type = row.get(CsvColumnNames.NAV_TYPE.value, "").strip()
                    category = row.get(CsvColumnNames.CATEGORY.value, "").strip()
                    is_enabled = row.get(CsvColumnNames.IS_ENABLED.value, "").strip()
                    url = row.get(CsvColumnNames.URL.value, "").strip()
                    comment = row.get(CsvColumnNames.COMMENT.value, None)

                    if not all([nav_type, category, is_enabled, url]):
                        print(f"⚠️ Some data are missing in: {selected_file_path}. A row is skipped: {row}")
                        continue

                    websites.append([nav_type, locale, category, is_enabled, url, comment])
        return websites

    @classmethod
    def get_domains_data(cls, config_ini_manager):
        selected_csv_files = cls.get_selected_csv_files(config_ini_manager)
        cls.locales = set()
        cls.domains = set()
        cls.include_global = False

        for selected_file_path in selected_csv_files:
            if not os.path.exists(selected_file_path):
                continue

            locale = os.path.splitext(os.path.basename(selected_file_path))[0].replace("-links", "").upper()
            if locale == "COMMON":
                cls.include_global = True
            else:
                cls.locales.add(locale)

            with open(selected_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]

                for row in reader:
                    if not row:
                        continue
                    url = row.get(CsvColumnNames.URL.value, "").strip()
                    domain = url.split("/")[2] if "//" in url else url
                    cls.domains.add(domain)

        return cls.locales, cls.domains, cls.include_global
