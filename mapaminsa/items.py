# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re
import pandas as pd
from itemloaders.processors import TakeFirst, MapCompose

ACRONYMS = {
    "H": "causas_egresos_hospitalarios_general",
    "M": "causas_egresos_maternos",
    "D": "causas_de_defuncion",
    "T": "tipos_tumores_malignos_general",
    "TT": "tipos_tumores_malignos_menores_de_15",
    "Ep": "enfermedades_epidemicas",
    "Inf": "enfermedades_infecciosas",
    "V": "immunizaciones",
    "VIH": "VIH",
    "C": "enfermedades_cronicas",
    "c": "enfermedades_cronicas",
    "P": "causas_egresos_hospitalarios_general"
}


# Helpers
def has_irrelevant_data(string):
    """
    Pattern matches string for data not needed in final tables.
    NOTE: NEEDED DONT DELETE
    """
    pattern = r'\b[a-zA-Z]{3,6}\b'
    row_to_drop_data = re.search(pattern, string)
    if not row_to_drop_data:
        return False
    word = row_to_drop_data.group(0).lower()
    if word == 'fuente':
        return True
    if word == 'total':
        return True
    if word == 'nan':
        return True
    return False
# Helpers


def extract_data_from(tag_string, cut_index=1, header=1):
    """
    Parse and extract numeric data from an HTML table.
    Before returning, clean and format the data.

    :NOTE: Strips off data source info because
    it's sometimes attached to the first column
    or the second column. Either way, the data source
    info does not contain link to the primary data.
    Omitting such information may be useless because
    there is no way to confirm it without access to
    it's primary source.

    :returns: JSON string
    """
    dfs = pd.read_html(tag_string, header=header)
    df = dfs[0]

    # Start cleaning data
    df = df.iloc[:, cut_index:].copy()
    df.columns = df.columns.str.lower().str.replace(',',
                                                    '').str.replace(' ', '_')

    # Drop row entry `total', `* fuente.. ', or `nan'
    df_last_row = df.tail(1).iloc[:, 0:1]
    column_name = df_last_row.columns[0]
    row_number = df.tail(1).iloc[:, 0:1].index[0]
    string_to_search = str(df.at[row_number, column_name])

    while has_irrelevant_data(string_to_search):
        df.drop(df.tail(1).index, inplace=True)  # drop last n rows, n=1
        df_last_row = df.tail(1).iloc[:, 0:1]
        column_name = df_last_row.columns[0]
        row_number = df.tail(1).iloc[:, 0:1].index[0]
        string_to_search = str(df.at[row_number, column_name])

    # Format data to return
    json_data = df.to_json(
        # index=False,
                           force_ascii=False,
                           orient='records')
    return json_data


def parse_title(attr_val):
    """"
    Extract data's title information.
    """
    matches = re.search(r'(?P<disease_name>[a-zA-Z]+)', attr_val, re.UNICODE)

    if not matches:
        # Add missing title if not found
        title = "enfermedades_cronicas"
    else:
        # TODO Possibility of KeyError if new table data added to page
        # CONFIRMED It happens 2 times with key 'x'
        disease_key = matches.group('disease_name')
        try:
            title = ACRONYMS[disease_key]
        except KeyError:
            if disease_key == "x":
                return ''
            else:
                raise ValueError(f"Can't find `{disease_key}` in `ACRONYMS`.")
    return title


def parse_year(attr_val):
    """
    Extract data's year information.
    """
    matches = re.search(r'(?P<year>20\d{2})', attr_val, re.UNICODE)
    return matches.group('year')


class MinsaItem(scrapy.Item):
    title = scrapy.Field(input_processor=MapCompose(parse_title),
                         output_processor=TakeFirst())
    year = scrapy.Field(input_processor=MapCompose(parse_year),
                        output_processor=TakeFirst())
    data = scrapy.Field(input_processor=MapCompose(extract_data_from),
                        output_processor=TakeFirst())
    location = scrapy.Field()
