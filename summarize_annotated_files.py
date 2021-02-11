#!/bin/env python

import os
import fnmatch
import argparse
import cga_util
import logging
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
import config as cfg
from googleapiclient.discovery import build
from google.oauth2 import service_account

# This script is here to streamline and automate the manual process of:
# 1. Running catalog_disk_usage.py
# 2. Running annotate_scan.py with the outputted .files.txt
# 3. Running Summarize.py with the outputted .annot.files.txt
# 4. Locating and downloading the .annot.summ.txt
# 5. Importing the .annot.summ.txt file into google sheets
<<<<<<< HEAD
=======
import logging.handlers
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
import config as cfg
from googleapiclient.discovery import build
from google.oauth2 import service_account
>>>>>>> 19c1fd6... finished google sheets api integration
=======
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22


def parse_args():
    """ Parse all the arguments from the command line. """
    parser = argparse.ArgumentParser(description='Catalog metadata of files within a given directory')
    parser.add_argument('-r', '--rootdir', required=True, help='Top directory to begin from')
    parser.add_argument('-o', '--outpath', required=True, help='Directory in which to put the catalog file.')
    parser.add_argument('-v', '--verbose', help='Report status', action="store_true")  # Verbose mode on if designated
    parser.add_argument('-d', '--debug', help='Debug mode', action="store_true")  # Debug mode on if designated
    args = parser.parse_args()
    return args


def find(pattern, path):
    """ Helper method to search for a file within a directory. """
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 19c1fd6... finished google sheets api integration
=======
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
def auth():
    """ Authorizes service account with Google Sheets API. """
    try:
        scopes = cfg.SCOPES
        secret = os.path.join(os.getcwd(), cfg.CLIENT_SECRET)
        credentials = service_account.Credentials.from_service_account_file(secret, scopes=scopes)
        service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)

        return service

    except Exception as e:
        logging.error(e)



def write_to_sheets(file):
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
    """ Writes .annot.summ.txt data into a google sheet. """
    spreadsheet_id = cfg.SPREADSHEET_ID
    service = auth()  
    file_name = os.path.basename(file)

    logging.info("Creating new sheet...")
    try:
        sheet_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': file_name,
                    }
                }
            }]
        }
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=sheet_body
        ).execute()

    except Exception as e:
        logging.error(e)
    
    
    logging.info("Writing to spreadsheet...")
    try:
        # getting new sheet data
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()  
        sheets = sheet_metadata.get('sheets', '')
        range = sheets[len(sheets) - 1].get("properties", {}).get("title")  # set the newly created sheet as the range
        # ssheet_id = sheets[len(sheets) - 1].get("properties", {}).get("sheetId")
        
        values = get_file_contents(file)  # gets contents of files and stores every line in a list
        body = {
           'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range, body=body, valueInputOption='USER_ENTERED'
        ).execute()

        logging.debug('{0} cells appended.'.format(result \
                                       .get('updates') \
                                       .get('updatedCells')))

    except Exception as e:
        logging.error(e)
    
    
def get_file_contents(file):
    """ Reads every line in a file and returns it as a 2d list. """
    logging.debug("Opening file: {}".format(file))

    values = []
    try:
        with open(file, 'r') as f:
            for line in f:
                values.append(line.split('\t'))
    except Exception as e:
        logging.error(e)

    return values


def parse_files(file, slice_index, outpath):
    """ Parses the outpath directory to find every file ran in the last minute. """
    start_range = len(file) - slice_index
    end_range = start_range + 2
    seconds = file[start_range:end_range]  # string slicing
    pattern = file.replace(seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    files_list = find(pattern, outpath)  # grabs files that matches the minute last ran

    return files_list
<<<<<<< HEAD
=======
def get_user_credentials():
    """ Returns the auth tokens for the Sheets API via the client_id file. """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def write_to_sheets(file, credentials):
=======
>>>>>>> 19c1fd6... finished google sheets api integration
    """ Writes .annot.summ.txt data into a google sheet. """
    spreadsheet_id = cfg.SPREADSHEET_ID
    service = auth()  
    file_name = os.path.basename(file)

    logging.info("Creating new sheet...")
    try:
        sheet_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': file_name,
                    }
                }
            }]
        }
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=sheet_body
        ).execute()

    except Exception as e:
        logging.error(e)
    
    
    logging.info("Writing to spreadsheet...")
    try:
        # getting new sheet data
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()  
        sheets = sheet_metadata.get('sheets', '')
        range = sheets[len(sheets) - 1].get("properties", {}).get("title")  # set the newly created sheet as the range
        # ssheet_id = sheets[len(sheets) - 1].get("properties", {}).get("sheetId")
        
        values = get_file_contents(file)  # gets contents of files and stores every line in a list
        body = {
           'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range, body=body, valueInputOption='USER_ENTERED'
        ).execute()

        logging.debug('{0} cells appended.'.format(result \
                                       .get('updates') \
                                       .get('updatedCells')))

    except Exception as e:
        logging.error(e)
    
    
def get_file_contents(file):
    """ Reads every line in a file and returns it as a 2d list. """
    logging.debug("Opening file: {}".format(file))

    values = []
    try:
        with open(file, 'r') as f:
            for line in f:
                values.append(line.split('\t'))
    except Exception as e:
        logging.error(e)

    return values


<<<<<<< HEAD
    return contents
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
def parse_files(file, slice_index, outpath):
    """ Parses the outpath directory to find every file ran in the last minute. """
    start_range = len(file) - slice_index
    end_range = start_range + 2
    seconds = file[start_range:end_range]  # string slicing
    pattern = file.replace(seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    files_list = find(pattern, outpath)  # grabs files that matches the minute last ran

    return files_list
>>>>>>> 19c1fd6... finished google sheets api integration
=======
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22


def main():
    """ Runs catalog_disk_usage.py, annotate_scan.py, and Summarize.py in this respective order.
    Also dumps the .annot.summ.txt file to a Google Sheet. """
    logger = logging.getLogger("")
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    logger.setLevel(logging.DEBUG)  # set level of logging to display in the console
=======
    logger.setLevel(logging.DEBUG)
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    logger.setLevel(logging.DEBUG)  # set level of logging to display in the console
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    logger.setLevel(logging.DEBUG)  # set level of logging to display in the console
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22

    args = parse_args()
    rootdir = args.rootdir  # root directory passed from user
    outpath = args.outpath  # output directory passed from user

    # Quick and dirty file paths fix.
    if rootdir[-1] != '/':
        rootdir += '/'
    if outpath[-1] != '/':
        outpath += '/'

    # construct the paths and file names
    rootdir_cleaned = rootdir.replace('/', '_')
    rootdir_cleaned = rootdir_cleaned[1:]
    outpath_name = rootdir_cleaned + '_' + cga_util.get_timestamp() + '.files.txt'  # output file only, no directory
    annot_outpath_name = rootdir_cleaned + '_' + cga_util.get_timestamp() + '.annot.files.txt'  # output file for annot
    summ_outpath_name = rootdir_cleaned + '_' + cga_util.get_timestamp() + '.annot.summ.txt'  # output file for summ

    # catalog_disc_usage.py
    cat_disk = "python3 catalog_disk_usage.py -r {} -o {}".format(rootdir, outpath)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    logging.info("#=================   catalog_disk_usage.py   =================#")
=======
    logging.info("@@@@@@@@@@@@@ catalog_disk_usage.py @@@@@@@@@@@@@")
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    logging.info("#=================   catalog_disk_usage.py   =================#")
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    logging.info("#=================   catalog_disk_usage.py   =================#")
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
    logging.debug(cat_disk)

    try:
        os.system(cat_disk)
    except Exception as e:
        logging.error(e)
        # TODO: add email support

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    outpath_files = parse_files(outpath_name, 12, outpath)  # grab all the files ran within the last minute
=======

    # surgically removing the seconds timestamp to find the .files.txt file
    out_r1 = len(outpath_name) - 12
    out_r2 = out_r1 + 2
    f_seconds = outpath_name[out_r1:out_r2]  # string slicing
    pattern = outpath_name.replace(f_seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    outpath_files = find(pattern, outpath)  # grab the first file that matches the minute last ran
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    outpath_files = parse_files(outpath_name, 12, outpath)  # grab all the files ran within the last minute
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    outpath_files = parse_files(outpath_name, 12, outpath)  # grab all the files ran within the last minute
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22

    if not outpath_files:  # check if outpath_files exist
        raise Exception("No .files.txt file found!")

    logging.debug(".files.txt: {}".format(outpath_files))

    # to prevent script from grabbing an .annot.files.txt file
    files_txt = []
    if len(outpath_files) > 1:
        for file in outpath_files:
            if file[len(file) - 13] == '_':
                files_txt.append(file)
        # now grab the latest file using max magic
        outpath_file = max(files_txt)
    else:
        outpath_file = outpath_files[0]

    logging.debug("Most recent .files.txt: {}".format(outpath_files))

    # annotate_scan.py
    annot_scan = "python3 annotate_scan.py {}".format(outpath_file)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    logging.info("#=================     annotate_scan.py     =================#")
    logging.debug(annot_scan)
    
=======
    logging.info("@@@@@@@@@@@@@ annotate_scan.py @@@@@@@@@@@@@")
    logging.debug(annot_scan)
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    logging.info("#=================     annotate_scan.py     =================#")
    logging.debug(annot_scan)
    
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    logging.info("#=================     annotate_scan.py     =================#")
    logging.debug(annot_scan)
    
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
    try:
        os.system(annot_scan)
    except Exception as e:
        logging.error(e)
        # TODO: add email support

    # surgically removing the seconds timestamp to find the .annot.files.txt file
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    a_outpath_files = parse_files(annot_outpath_name, 18, outpath)
=======
    a_out_r1 = len(annot_outpath_name) - 18
    a_out_r2 = a_out_r1 + 2
    a_seconds = annot_outpath_name[a_out_r1:a_out_r2]  # string slicing
    pattern = annot_outpath_name.replace(a_seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    a_outpath_files = find(pattern, outpath)  # grab the files that were run in the same minute
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    a_outpath_files = parse_files(annot_outpath_name, 18, outpath)
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    a_outpath_files = parse_files(annot_outpath_name, 18, outpath)
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
    logging.debug(".annot.files.txt: {}".format(a_outpath_files))
    a_outpath_file = max(a_outpath_files)  # grabs the file that is the latest one in the last minute
    logging.debug("Most recent .annot.files.txt: {}".format(a_outpath_file))

    # Summarize.py
    summarize = "python3 Summarize.py {}".format(a_outpath_file)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    logging.info("#=================       Summarize.py       =================#")
    logging.debug(summarize)
    
=======
    logging.info("@@@@@@@@@@@@@ Summarize.py @@@@@@@@@@@@@")
    logging.debug(summarize)
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    logging.info("#=================       Summarize.py       =================#")
    logging.debug(summarize)
    
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    logging.info("#=================       Summarize.py       =================#")
    logging.debug(summarize)
    
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
    try:
        os.system(summarize)
    except Exception as e:
        logging.error(e)
        # TODO: add email support

    # surgically removing the seconds timestamp to find the .annot.files.txt file
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    
    s_outpath_files = parse_files(summ_outpath_name, 17, outpath)
    logging.debug(".annot.summ.txt: {}".format(s_outpath_files))
    s_outpath_file = max(s_outpath_files)  # grabs the file that is the latest one in the last minute
    logging.debug("Most recent .annot.summ.txt: {}".format(s_outpath_file))

    logging.info("#================= Importing to Google Sheets =================#")
    logging.debug("Importing: {}".format(s_outpath_file))
    write_to_sheets(s_outpath_file)

    logging.info("#=================       END OF SCRIPT       =================#")
=======
    s_out_r1 = len(summ_outpath_name) - 17
    s_out_r2 = s_out_r1 + 2
    s_seconds = summ_outpath_name[s_out_r1:s_out_r2]  # string slicing
    pattern = summ_outpath_name.replace(s_seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    s_outpath_files = find(pattern, outpath)  # grab the files that were run in the same minute
    logging.debug(".annot.summ.txt: {}".format(a_outpath_files))
=======
    
    s_outpath_files = parse_files(summ_outpath_name, 17, outpath)
    logging.debug(".annot.summ.txt: {}".format(s_outpath_files))
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    
    s_outpath_files = parse_files(summ_outpath_name, 17, outpath)
    logging.debug(".annot.summ.txt: {}".format(s_outpath_files))
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22
    s_outpath_file = max(s_outpath_files)  # grabs the file that is the latest one in the last minute
    logging.debug("Most recent .annot.summ.txt: {}".format(s_outpath_file))

    logging.info("#================= Importing to Google Sheets =================#")
    logging.debug("Importing: {}".format(s_outpath_file))
    write_to_sheets(s_outpath_file)

<<<<<<< HEAD
<<<<<<< HEAD
    logging.info("@@@@@@@@@@@@@ END OF SCRIPT @@@@@@@@@@@@@")
>>>>>>> 8782c29... added google api auths- wip not working yet
=======
    logging.info("#=================       END OF SCRIPT       =================#")
>>>>>>> 19c1fd6... finished google sheets api integration
=======
    logging.info("#=================       END OF SCRIPT       =================#")
>>>>>>> 3570b7f11d84ad10222b52fba42ea3a4a7f45b22


if __name__ == '__main__':
    main()
