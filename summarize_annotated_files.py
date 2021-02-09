#!/bin/env python

import os
import fnmatch
import argparse
import cga_util
import logging
import logging.handlers
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


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
    """ Writes .annot.summ.txt data into a google sheet. """
    service = build('sheets', 'v4', credentials=credentials)
    # create spreadsheet
    logging.info("Creating spreadsheet...")
    spreadsheet = {
        'properties': {
            'title': file  # TODO: slice filepath from string
        }
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    logging.debug('Spreadsheet ID: {0}'.format(spreadsheet.get('spreadsheetId')))

    # TODO: append every line from .annot.summ.txt file into sheet
    get_file_contents(file)


def get_file_contents(file):
    logging.debug("Opening file: {}".format(file))

    contents = []
    f = open(file, 'r')
    for line in f:
        contents.append(line)
    f.close()

    return contents


def main():
    """ Runs catalog_disk_usage.py, annotate_scan.py, and Summarize.py in this respective order.
    Also dumps the .annot.summ.txt file to a Google Sheet. """
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)

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
    logging.info("@@@@@@@@@@@@@ catalog_disk_usage.py @@@@@@@@@@@@@")
    logging.debug(cat_disk)

    try:
        os.system(cat_disk)
    except Exception as e:
        logging.error(e)
        # TODO: add email support


    # surgically removing the seconds timestamp to find the .files.txt file
    out_r1 = len(outpath_name) - 12
    out_r2 = out_r1 + 2
    f_seconds = outpath_name[out_r1:out_r2]  # string slicing
    pattern = outpath_name.replace(f_seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    outpath_files = find(pattern, outpath)  # grab the first file that matches the minute last ran

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
    logging.info("@@@@@@@@@@@@@ annotate_scan.py @@@@@@@@@@@@@")
    logging.debug(annot_scan)
    try:
        os.system(annot_scan)
    except Exception as e:
        logging.error(e)
        # TODO: add email support

    # surgically removing the seconds timestamp to find the .annot.files.txt file
    a_out_r1 = len(annot_outpath_name) - 18
    a_out_r2 = a_out_r1 + 2
    a_seconds = annot_outpath_name[a_out_r1:a_out_r2]  # string slicing
    pattern = annot_outpath_name.replace(a_seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    a_outpath_files = find(pattern, outpath)  # grab the files that were run in the same minute
    logging.debug(".annot.files.txt: {}".format(a_outpath_files))
    a_outpath_file = max(a_outpath_files)  # grabs the file that is the latest one in the last minute
    logging.debug("Most recent .annot.files.txt: {}".format(a_outpath_file))

    # Summarize.py
    summarize = "python3 Summarize.py {}".format(a_outpath_file)
    logging.info("@@@@@@@@@@@@@ Summarize.py @@@@@@@@@@@@@")
    logging.debug(summarize)
    try:
        os.system(summarize)
    except Exception as e:
        logging.error(e)
        # TODO: add email support

    # surgically removing the seconds timestamp to find the .annot.files.txt file
    s_out_r1 = len(summ_outpath_name) - 17
    s_out_r2 = s_out_r1 + 2
    s_seconds = summ_outpath_name[s_out_r1:s_out_r2]  # string slicing
    pattern = summ_outpath_name.replace(s_seconds, '*')  # replacing the seconds in the timestamp with a wildcard
    s_outpath_files = find(pattern, outpath)  # grab the files that were run in the same minute
    logging.debug(".annot.summ.txt: {}".format(a_outpath_files))
    s_outpath_file = max(s_outpath_files)  # grabs the file that is the latest one in the last minute
    logging.debug("Most recent .annot.summ.txt: {}".format(a_outpath_file))


    logging.info("Importing {} to google sheets...")
    write_to_sheets(s_outpath_file, get_user_credentials())

    logging.info("@@@@@@@@@@@@@ END OF SCRIPT @@@@@@@@@@@@@")


if __name__ == '__main__':
    main()
