import json
import logging

from . import google_services
from .configs import META_SPREADSHEET_COL_DEFS, META_DATABASE_NAME, META_TABLE_NAME

logger = logging.getLogger(__name__)


def get_or_default(arr, index, default_value=None):
    """
    Get value at index from list. Return default value if index out of bound

    :type arr: list
    :param arr: List to get value from
    :type index: int
    :param index: Index to get value for
    :type default_value: Any
    :param default_value: Default value
    :rtype: Any
    :return: Value to get
    """
    return arr[index] if len(arr) > index else default_value


def get_col_index(col_name, col_defs):
    """
    Get index of column for a column name in a table.

    :type col_name: str
    :param col_name: Column name to get column definition for
    :type col_defs: list[dict]
    :param col_defs: Column definitions for table
    :rtype: int
    :return: Index of column. None if not found.
    """

    return next(iter([i for i in range(len(col_defs)) if col_defs[i]['name'] == col_name]), None)


def convert_to_value(raw_value, value_type):
    """
    Convert raw values into the correct type.

    :type raw_value: Any
    :param raw_value: Raw value to convert
    :type value_type: str
    :param value_type: Type to convert raw value to
    :rtype: Any
    :return: Converted value
    """

    if raw_value is None:
        return raw_value

    if value_type == 'string':
        return str(raw_value)
    elif value_type == 'number':
        return float(raw_value)
    elif value_type == 'datetime':
        # Simple string value for datetime for now
        return str(raw_value)
    elif value_type == 'json':
        return json.loads(raw_value)
    else:
        logger.warning('Unrecognised value type {} when converting raw value'.format(value_type))
        return raw_value


class SheetsdbSDKError(Exception):
    """
    Error raised by SDK
    """

    # Error codes
    SPREADSHEET_NOT_FOUND = 1
    UNEXPECTED_TABLE_RESULT = 2
    SHEETS_API_ERROR = 3

    def __init__(self, message, error_code, source='Unknown'):
        """
        :type message: str
        :param message: Error message
        :type error_code: int
        :param error_code: Error code
        :type source: str
        :param source: SDK function that error is raised from
        """

        super(SheetsdbSDKError, self).__init__(message)
        self.error_code = error_code
        self.source = source


class SheetsdbSDK:
    """
    SDK for all sheetsdb operations.
    """

    _logger = logging.getLogger('{}.{}'.format(__name__, __qualname__))

    def __init__(self, user, meta_spreadsheet):
        """
        :type user: django.contrib.auth.models.User
        :param user: User to create SDK for
        :type meta_spreadsheet: dict
        :param meta_spreadsheet: Google `Spreadsheet` resource
        """

        if user is None:
            raise ValueError('user is none')
        if meta_spreadsheet is None:
            raise ValueError('meta_spreadsheet is None')

        self._user = user
        self._meta_spreadsheet = meta_spreadsheet
        self._tables = dict()

    def _create_table(self, spreadsheet_id, col_defs):
        """
        Internal function.

        Create a table by reading a spreadsheet.

        :type spreadsheet_id: str
        :param spreadsheet_id: Spreadsheet ID containing table data
        :type col_defs: list[dict]
        :param col_defs: List of column definitions for table
        :rtype: Table
        :return: Created table
        """

        value_range, error_status = google_services.get_columns_values(self._user, spreadsheet_id, 0, len(col_defs) - 1)
        if error_status is None:
            return Table(spreadsheet_id, value_range, col_defs)
        elif error_status == 404:
            raise SheetsdbSDKError('Spreadsheet {} not found'.format(spreadsheet_id),
                                   SheetsdbSDKError.SPREADSHEET_NOT_FOUND, 'get_table_defs')
        else:
            raise SheetsdbSDKError('Sheets API error {}'.format(error_status),
                                   SheetsdbSDKError.SHEETS_API_ERROR, 'get_table_defs')

    def get_meta_spreadsheet_id(self):
        """
        :rtype: str
        :return: Meta spreadsheet ID
        """

        return self._meta_spreadsheet['spreadsheetId']

    def get_meta_table(self):
        """
        Get the meta table

        :rtype: Table
        :return: Meta table
        """

        if self._tables.get(META_DATABASE_NAME, {}).get(META_TABLE_NAME) is None:
            # Create table
            meta_spreadsheet_id = self.get_meta_spreadsheet_id()
            if not hasattr(self._tables, META_DATABASE_NAME):
                self._tables[META_DATABASE_NAME] = {}
            self._tables[META_DATABASE_NAME][META_TABLE_NAME] = self._create_table(
                meta_spreadsheet_id, META_SPREADSHEET_COL_DEFS)

        return self._tables[META_DATABASE_NAME][META_TABLE_NAME]

    def get_table(self, database_name, table_name):
        """
        Get a table from a database

        :type database_name: str
        :param database_name: Name of database to get table from
        :type table_name: str
        :param table_name: Name of table to get
        :rtype: Table
        :return: Table to get
        """

        if self._tables.get(database_name, {}).get(table_name) is None:
            # Create table
            # Get column definitions for table
            meta_table = self.get_meta_table()
            row_based_result = meta_table.select(
                ['spreadsheet_id', 'col_defs'],
                [WhereCondition('database_name', database_name), WhereCondition('table_name', table_name)])
            if len(row_based_result) != 1:
                raise SheetsdbSDKError(
                    'Expected 1 row for col_defs but got {}'.format(len(row_based_result)),
                    SheetsdbSDKError.UNEXPECTED_TABLE_RESULT, 'get_table')
            row = row_based_result[0]
            if not hasattr(self._tables, database_name):
                self._tables[database_name] = {}
            self._tables[database_name][table_name] = self._create_table(row['spreadsheet_id'], row['col_defs'])

        return self._tables[database_name][table_name]

    def get_num_tables(self, database_name):
        """
        Get the number of tables in a database

        :type database_name: str
        :param database_name: Name of database to get number of tables for
        :rtype: int
        :return: Number if tables in database specified
        """

        if database_name is None:
            raise ValueError('database_name is None')

        row_based_result = self.get_meta_table().select(['table_name'], [WhereCondition('table_name', database_name)])
        return len(row_based_result)

    def get_all_tables_info(self):
        """
        Get information of all tables in the form:

            [
                {
                    'database_name': ... ,
                    'table_name': ... ,
                    'spreadsheet_id': ... ,
                    'col_defs':
                        [
                            {
                                'name': ... ,
                                'type': ... ,
                            },

                            ...
                        ],
                },

                ...
            ]

        :rtype: list[dict]
        :return: List of information of all tables
        """

        meta_table = self.get_meta_table()
        return meta_table.select(['database_name', 'table_name', 'spreadsheet_id', 'col_defs'])


class Table:
    """
    Logical table entity for a database table.
    When created, it captures a Google `ValueRange` resource and stores it as the initial state of the table.
    Provides functions to operate on the table in memory and commit the changes to Google Sheets.
    """

    _logger = logging.getLogger('{}.{}'.format(__name__, __qualname__))

    def __init__(self, spreadsheet_id, value_range, col_defs):
        """
        :type spreadsheet_id: str
        :param spreadsheet_id: Spreadsheet ID of spreadsheet containing table data. Only when committing changes.
        :type value_range: Google `ValueRange` resource
        :param value_range: Table data
        :type col_defs: list[dict]
        :param col_defs: List of column definitions for table
        """

        if spreadsheet_id is None:
            raise ValueError('spreadsheet_id is None')
        if value_range is None:
            raise ValueError('value_range is None')
        if col_defs is None:
            raise ValueError('col_defs is None')
        major_dimension = value_range.get('majorDimension')
        if not major_dimension == 'ROWS':
            raise ValueError('Wrong major dimension {}. Should be ROWS'.format(major_dimension))

        self.spreadsheet_id = spreadsheet_id
        self.col_defs = col_defs
        self.col_names = [col_def['name'] for col_def in col_defs]
        self.rows = value_range.get('values', [])
        self._reset_changes()

    def _reset_changes(self):
        self.inserted_rows = []
        self.deleted_row_indexes = set()
        self.updated_row_indexes = set()

    def _get_effective_rows(self):
        return [self.rows[i] for i in range(len(self.rows)) if i not in self.deleted_row_indexes] + self.inserted_rows

    def num_rows(self):
        """
        :rtype: int
        :return: Number of rows in table
        """

        return len(self._get_effective_rows())

    def select(self, col_names, where_conditions=list(), is_row_base=True):
        """
        Select some data from table and return it as a row-based or column-based format.

        If row-based format, returned data is:
            [
                {
                    col_1: row_1_value,
                    ...
                    col_c: row_1_value,
                },

                ...

                {
                    col_1: row_r_value,
                    ...
                    col_c: row_r_value,
                },
            ]

        If column-based format, returned data is:
            {
                col_1: [row_1_value, ... row_r_value],

                ...

                col_c: [row_1_value, ... row_r_value],
            }

        :type col_names: list[str]
        :param col_names: List of valid column names to select
        :type where_conditions: list[WhereCondition]
        :param where_conditions: List of where conditions for that each row must satisfy query
        :type is_row_base: bool
        :param is_row_base: Whether result is row based. False indicated result is column-based.
        :rtype: list or dict
        :return: Row-based or column-based result

        """

        if not set(col_names).issubset(self.col_names):
            raise ValueError('Invalid column name for select query')

        if len(col_names) == 0:
            self._logger.debug('No column name to select. Return empty result set')
            return [] if is_row_base else {}

        # Construct effect rows by removing deleted rows and adding inserted rows
        effective_rows = self._get_effective_rows()
        filtered_rows = [row for row in effective_rows
                         if all([condition.is_pass(row, self.col_defs) for condition in where_conditions])]
        col_indexes = [get_col_index(col_name, self.col_defs) for col_name in col_names]
        if is_row_base:
            result = []
            for row in filtered_rows:
                row_data = {}
                for i in col_indexes:
                    row_data[self.col_defs[i]['name']] = convert_to_value(
                        get_or_default(row, i), self.col_defs[i]['type'])
                result.append(row_data)
        else:
            result = {}
            for i in col_indexes:
                column_data = []
                for row in filtered_rows:
                    column_data.append(convert_to_value(
                        get_or_default(row, i), self.col_defs[i]['type']))
                result[self.col_defs[i]['name']] = column_data

        return result

    def insert(self, row_data):
        """
        Insert a row of data. Row data is in the form:
        {
            'col_name': value,
            ...
        }

        :type row_data: dict
        :param row_data: A dict where key is a valid column name and value is the value to be inserted for that column.
            All column names must be valid.
            Not all column names need to be specified. Not specified columns names are set to None.
        """

        if not set(row_data.keys()).issubset(self.col_names):
            raise ValueError('Invalid column name for row to insert')

        self.inserted_rows.append(
            [row_data[col_def['name']] if col_def['name'] in row_data else None for col_def in self.col_defs])

    def commit(self, user):
        """
        Commits any the changes made to Google Sheets. Multiple commits is allowed and results in incremental update.

        :type user: django.contrib.auth.models.User
        :param user: User of spreadsheet containing table data
        """

        # Update
        # Do first as required original row indexes to identify rows to update
        if len(self.updated_row_indexes) > 0:
            update_response, update_error_status = google_services.update_rows(
                user, self.spreadsheet_id,
                [
                    {
                        'index': updated_row_index,
                        'values': self.rows[updated_row_index],
                    } for updated_row_index in self.updated_row_indexes
                ])
            if update_error_status is not None:
                raise SheetsdbSDKError('Sheets API error {} when updating updated rows'.format(update_error_status),
                                       SheetsdbSDKError.SHEETS_API_ERROR, '{}{}'.format(self.__qualname__, 'commit'))

        # Delete
        # Also require original row indexes to identify rows to update
        # but comes after update as deleting will change the row indexes
        if len(self.deleted_row_indexes) > 0:
            delete_response, delete_error_status = google_services.delete_rows(
                user, self.spreadsheet_id, self.deleted_row_indexes)
            if delete_error_status is not None:
                raise SheetsdbSDKError('Sheets API error {} when deleting deleted rows'.format(delete_error_status),
                                       SheetsdbSDKError.SHEETS_API_ERROR, '{}{}'.format(self.__qualname__, 'commit'))

        # Insert last as it is just an append operation
        if len(self.inserted_rows) > 0:
            insert_response, insert_error_status = google_services.insert_rows(
                user, self.spreadsheet_id, self.inserted_rows)
            if insert_error_status is not None:
                raise SheetsdbSDKError('Sheets API error {} when inserted inserted rows'.format(insert_error_status),
                                       SheetsdbSDKError.SHEETS_API_ERROR, '{}{}'.format(self.__qualname__, 'commit'))

        # Update rows and reset changes when all Sheets API requests succeed
        self.rows = self._get_effective_rows()
        self._reset_changes()


class WhereCondition:

    def __init__(self, col_name, value, comparator='='):
        """
        :type col_name: str
        :param col_name: Column name to check in where condition
        :type value: Any
        :param value: Value to check in where condition
        :type comparator: str
        :param comparator: '=' for all, '<=', '<', '>', '>=' for number values
        """
        if value is None:
            raise ValueError('value is None')
        if col_name is None:
            raise ValueError('col_name is None')
        if comparator not in ('=', '<=', '<', '>', '>='):
            raise ValueError('Unrecognised comparator {}'.format(comparator))

        self.value = value
        self.col_name = col_name
        self.comparator = comparator

    def is_pass(self, row, col_defs):
        """
        Check if row passes where condition

        :type row: list
        :param row: Row to check
        :type col_defs: list[dict]
        :param col_defs: Column definitions for table
        :rtype: bool
        :return: Whether row passes where condition
        """

        if col_defs is None:
            raise ValueError('col_defs is None')
        col_index = get_col_index(self.col_name, col_defs)
        if col_index is None:
            raise ValueError('Column name {} is not in column definitions'.format(self.col_name))
        col_type = col_defs[col_index]['type']
        if col_type == 'json':
            raise ValueError('json column type cannot be used in where condition')
        if not self.comparator == '=' and not col_type == 'int':
            raise ValueError('Illegal comparator {} for column type {}'.format(self.comparator, col_type))

        col_value = convert_to_value(row[col_index], col_type)
        if self.comparator == '=':
            return col_value == self.value
        elif self.comparator == '<=':
            return col_value <= self.value
        elif self.comparator == '<':
            return col_value < self.value
        elif self.comparator == '>':
            return col_value > self.value
        elif self.comparator == '>=':
            return col_value >= self.value
        else:
            raise RuntimeError(
                'Undetected mistake in where condition for column name {}, value {}, comparator {}.'.format(
                    self.col_name, self.value, self.comparator))
