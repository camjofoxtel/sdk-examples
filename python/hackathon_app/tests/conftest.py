import base64
import json
import os
import pytest  # type: ignore
from typing import Sequence

from google.oauth2 import service_account  # type: ignore
from googleapiclient import discovery  # type: ignore
from sheets import (
    Hackathon,
    Registrant,
    Registrations,
    Sheets,
    User,
    Users,
    WhollySheet,
)


@pytest.fixture(scope="module", name="WhollySheet")
def instantiate_whollysheet(spreadsheet_client, spreadsheet):
    """Creates and returns an instance of WhollySheet"""

    client = spreadsheet_client.values()
    return WhollySheet(
        client=client,
        spreadsheet_id=spreadsheet["spreadsheetId"],
        sheet_name="users",
        structure=Sequence[User],
    )


@pytest.fixture(scope="module", name="sheets")
def instantiate_sheets(spreadsheet, cred_file):
    """Creates and returns an instance of Sheets"""
    spreadsheet = spreadsheet
    return Sheets(spreadsheet_id=spreadsheet["spreadsheetId"], cred_file=cred_file)


@pytest.fixture(scope="module", name="users")
def instantiate_users(spreadsheet_client, spreadsheet):
    """Creates and returns an instance of Users"""
    client = spreadsheet_client.values()
    return Users(client=client, spreadsheet_id=spreadsheet["spreadsheetId"])


@pytest.fixture(scope="module", name="registrations")
def instantiate_registrations(spreadsheet_client, spreadsheet):
    """Creates and returns an instance of Registrations"""
    client = spreadsheet_client.values()
    return Registrations(client=client, spreadsheet_id=spreadsheet["spreadsheetId"])


@pytest.fixture(scope="module", name="spreadsheet")
def create_test_sheet(test_data, spreadsheet_client, drive_client):
    """Create a test sheet and populated it with test data"""
    request = spreadsheet_client.create(body=test_data)
    response = request.execute()

    yield response

    drive_client.files().delete(fileId=response["spreadsheetId"]).execute()


@pytest.fixture(name="test_users")
def get_test_users(test_data):
    """Returns a list of dicts representing the users sheet"""
    users_sheet = test_data["sheets"][0]
    assert users_sheet["properties"]["title"] == "users"
    return create_sheet_repr(users_sheet, User)


@pytest.fixture(name="test_hackathons")
def get_test_hackathons(test_data):
    """Returns a list of dicts representing the hackathons sheet"""
    hackathons_sheet = test_data["sheets"][1]
    assert hackathons_sheet["properties"]["title"] == "hackathons"
    return create_sheet_repr(hackathons_sheet, Hackathon)


@pytest.fixture(name="test_registrants")
def get_test_registrants(test_data):
    """Returns a list of dicts representing the registrations sheet"""
    registrations_sheet = test_data["sheets"][2]
    assert registrations_sheet["properties"]["title"] == "registrations"
    return create_sheet_repr(registrations_sheet, Registrant)


def create_sheet_repr(sheet, klass):
    """Converts a JSON representation of a sheet into a list of dicts. Each element
    in the list represents a row in the sheet, where each cell value can be accessed
    using the cell header as a key
    """
    header = get_header(sheet)
    data = get_data(sheet)
    result = [klass(**dict(zip(header, d))) for d in data]
    return result


def get_header(sheet):
    """Get the header as a list"""
    sheet_header = sheet["data"][0]["rowData"][0]["values"]
    header = []
    for cell in sheet_header:
        cell_value = cell["userEnteredValue"]["stringValue"]
        header.append(cell_value)
    return header


def get_data(sheet):
    """Return data (exc headers) from a sheet as a list of rows, with each
     row being a list representing all cell values in that row
     """
    rows_exc_header = sheet["data"][0]["rowData"][1:]
    data = []
    for row in rows_exc_header:
        row_data = []
        for cell in row["values"]:
            cell_value = cell["userEnteredValue"]["stringValue"]
            row_data.append(cell_value)
        data.append(row_data)
    return data


@pytest.fixture(name="test_data", scope="session")
def get_test_data():
    """Load the test data"""
    with open("tests/data/data.json", "r") as f:
        data = json.load(f)
    return data


@pytest.fixture(scope="session")
def spreadsheet_client(credentials):
    """Create a resource object to use the sheets API"""
    service = discovery.build("sheets", "v4", credentials=credentials)
    spreadsheet_client = service.spreadsheets()

    return spreadsheet_client


@pytest.fixture(scope="session")
def drive_client(credentials):
    """Create a resource object to use the drive API"""
    drive_client = discovery.build("drive", "v3", credentials=credentials)

    return drive_client


@pytest.fixture(scope="session")
def credentials(cred_file) -> service_account.Credentials:
    """Build a Credentials instance from file"""
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    credentials = service_account.Credentials.from_service_account_file(
        cred_file, scopes=scopes
    )

    return credentials


@pytest.fixture(scope="session")
def cred_file() -> str:
    """Read the google json credentials file (base64 encoded) from the
    GOOGLE_APPLICATION_CREDENTIAL_ENCODED env variable, decode it and write
    it to google-creds.json
    """
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIAL_ENCODED")
    assert google_creds
    file_name = "./google-creds.json"
    with open(file_name, "wb") as f:
        f.write(base64.b64decode(google_creds))

    yield file_name

    os.remove("./google-creds.json")
