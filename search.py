import sys
import quip
import os
import subprocess
import http
import urllib
import csv
from bs4 import BeautifulSoup


#####################################################################
## Constants
#####################################################################
TEXT_INDENT = " - "
CONFIG_FILENAME = ".search.py.settings"
CONFIG_KEY_QUIP_ACCESS_TOKEN = "QUIP_ACCESS_TOKEN"
CONFIG_KEY_QUIP_URL_STRIP = "QUIP_URL_STRIP"
CONFIG_KEY_SFDC_USERNAME = "SFDC_USERNAME"
CONFIG_KEY_SFDC_QUERY = "SFDC_QUERY"
CONFIG_KEY_KEYWORDS = "KEYWORDS"
CONFIG_KEY_MAX_RESULTS = "MAX_RESULTS"
CONFIG_KEY_CACHE_DIR = "CACHE_DIR"


#####################################################################
## Main Logic
#####################################################################
def main():
    print("search.py")
    print()

    print ("Usage: search.py [<search_term> .......]")
    print ("<search_term> can be repeated to incorporate searching on as many terms as desired")
    print ()

    config = load_config()

    # pull from command-line first
    searchTerms = sys.argv
    del searchTerms[0]

    # append from config file
    searchTerms = searchTerms + config[CONFIG_KEY_KEYWORDS].strip().split(",")

    if (len(searchTerms) == 0):
        print ("At least one search term is required, either via command line or in the properties file!")
        sys.exit()

    print ("Search Terms:")
    for searchTerm in searchTerms:
        print(TEXT_INDENT + searchTerm)
    print()

    cacheDir = config[CONFIG_KEY_CACHE_DIR]
    if (len(cacheDir) == 0):
        print ("Cache Directory is empty but required!")
        sys.exit()

    quipAccessToken = config[CONFIG_KEY_QUIP_ACCESS_TOKEN].strip()

    sfdcCsvText = sfdc_query(cacheDir, config)
    results = sfdcCsvText.splitlines()
    header = results[0]
    del results[0]

    outputHeader = header.split(",")
    outputHeader = outputHeader + searchTerms
    output = [ outputHeader ]

    maxResults = int(config[CONFIG_KEY_MAX_RESULTS].strip())

    numResults = 0
    for line in csv.reader(results, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True):
        accountId = line[0].strip()
        accountName = line[1].strip()
        accountSubRegion = line[2].strip()
        accountPlanUrl = line[3].strip()
        csPlanUrl = line[4].strip()

        o = process_account(cacheDir, quipAccessToken, config[CONFIG_KEY_QUIP_URL_STRIP].strip(), accountId, accountName, accountSubRegion, accountPlanUrl, csPlanUrl, searchTerms)
        output.append(o)

        numResults += 1
        if (maxResults != 0) and (numResults >= maxResults):
            print ("Max Results Limit reached: " + str(maxResults))
            break

    print ("Number of lines: " + str(len(output)))
    outputFilename = cacheDir + "/report.csv"
    delete_file(outputFilename)
    with open(outputFilename, "x") as csvFile:
        csvWriter = csv.writer(csvFile, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL)
        for line in output:
            line = [x.strip() for x in line]
            csvWriter.writerow(line)

    print ("CSV Output Complete!")


#####################################################################
# Deletes the file from disk, if it exists
#####################################################################
def delete_file(filename):
    try:
        os.remove(filename)
    except FileNotFoundError:
        return

#####################################################################
# Cache the specified AP document
#####################################################################
def cache_ap(cacheDir, accountId, apText):

    filename = cacheDir + "/" + accountId + "_ap.html"
    with open(filename, 'x') as f:
        f.write(apText)


#####################################################################
# Cache the specified cs document
#####################################################################
def cache_cs(cacheDir, accountId, csText):

    filename = cacheDir + "/" + accountId + "_cs.html"
    with open(filename, 'x') as f:
        f.write(csText)


#####################################################################
# Gets the cached AP if it exists
#####################################################################
def get_cached_ap(cacheDir, accountId):
    filename = cacheDir + "/" + accountId + "_ap.html"

    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


#####################################################################
# Gets the cached CS if it exists
#####################################################################
def get_cached_cs(cacheDir, accountId):
    filename = cacheDir + "/" + accountId + "_cs.html"

    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


#####################################################################
## Process account record
#####################################################################
def process_account(cacheDir, accessToken, quipUrlStrip, accountId, accountName, accountSubRegion, accountPlanUrl, csPlanUrl, searchTerms):
    matches = 0

#    print ("Cache Dir: " + cacheDir)
#    print ("Access Token: " + accessToken)
#    print ("Quip URL Strip: " + quipUrlStrip)
#    print ("Account ID: " + accountId)
#    print ("Account Name: " + accountName)
#    print ("Account Sub Region: " + accountSubRegion)
#    print ("Account Plan URL: " + accountPlanUrl)
#    print ("CS Plan URL: " + csPlanUrl)

    line = [ accountId, accountName, accountSubRegion, accountPlanUrl, csPlanUrl]
    lineSearchTerms = [ ]
    for searchTerm in searchTerms:
        lineSearchTerms = lineSearchTerms + [ 0 ]

# the built in search functionality for quip does not work well at all, FYI.  Reminds me of searching reddit.
#    for searchTerm in searchTerms:
#        search_quip(config[CONFIG_KEY_QUIP_ACCESS_TOKEN], searchTerm, config["TEST_DOC_ID"].casefold())

    # Download AP Plan
    accountPlan = get_cached_ap(cacheDir, accountId)
    if (len(accountPlan) > 0):
        print("Using AP Cache: " + accountId)
    else:
        if (len(accountPlanUrl) > 0):
            u = accountPlanUrl.replace(quipUrlStrip, "")
            t = u.split("/", 1)
            if (len(t) > 1):
                docId = t[0]
            else:
                docId = u
            print ("AP URL=" + accountPlanUrl + " U=" + u + " DocID=" + docId)
            try:
                accountPlan = get_quip_doc(accessToken, docId)
                cache_ap(cacheDir, accountId, accountPlan)
            except http.client.InvalidURL:
                print ("Account Plan URL invalid!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + accountPlanUrl)
            except quip.QuipError:
                print ("Unable to access Account Plan URL, likely due to permissions!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + accountPlanUrl)
            except urllib.error.HTTPError:
                print ("Internal Server Error when pulling Account Plan URL!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + accountPlanUrl)
            except TimeoutError:
                print ("Timeout Error while pulling Account Plan URL!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + accountPlanUrl)

    # Download CS Plan
    csPlan = get_cached_cs(cacheDir, accountId)
    if (len(csPlan) > 0):
        print("Using CS Cache: " + accountId)
    else:
        if (len(csPlanUrl) > 0):
            u = csPlanUrl.replace(quipUrlStrip, "")
            t = u.split("/", 1)
            if (len(t) > 1):
                docId = t[0]
            else:
                docId = u
            print ("CS Doc ID = " + docId)
            try:
                csPlan = get_quip_doc(accessToken, docId)
                cache_cs(cacheDir, accountId, csPlan)
            except http.client.InvalidURL:
                print ("CS Plan URL invalid!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + csPlanUrl)
            except quip.QuipError:
                print ("Unable to access CS Plan URL, likely due to permissions!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + csPlanUrl)
            except urllib.error.HTTPError:
                print ("Internal Server Error when pulling CS Plan URL!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + csPlanUrl)
            except TimeoutError:
                print ("Timeout Error while pulling CS Plan URL!  AccountID=" + accountId + " AccountName=" + accountName + " URL=" + csPlanUrl)

    accountPlanSoup = None
    if (accountPlan != ""):
        accountPlanSoup = BeautifulSoup(accountPlan, features="html.parser")
    csPlanSoup = None
    if (csPlan != ""):
        csPlanSoup = BeautifulSoup(csPlan, features="html.parser")

    searchTermIndex = 0
    for searchTerm in searchTerms:
        count = 0
        if (accountPlanSoup != None):
            count += accountPlanSoup.get_text().casefold().count(searchTerm.casefold())
        if (csPlanSoup != None):
            count += csPlanSoup.get_text().casefold().count(searchTerm.casefold())

        lineSearchTerms[searchTermIndex] = count
        searchTermIndex += 1

    lineSearchTerms = [str(x) for x in lineSearchTerms]
    return line + lineSearchTerms


#####################################################################
## Query SFDC for a list of Quip Documents to search
#####################################################################
def sfdc_query(cacheDir, config):

    sqlQuery = config[CONFIG_KEY_SFDC_QUERY].strip()
    if (sqlQuery.casefold()[:6] != "select"):
        print ("Only SELECT statements are appropriate for use!  Query=" + sqlQuery)
        sys.exit()
    else:
        print ("SOQL statement validated to to be a query...")
    
    print ("Executing SOQL query to search for Quip documents now using SFDX...  Expecting that you have already authenticated prior to running this script.")
    command = [
        "sfdx",
        "data:soql:query",
        "-q",
        sqlQuery,
        "-o",
        config[CONFIG_KEY_SFDC_USERNAME].strip(),
        "-r",
        "csv"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderrr = process.communicate()
    if (process.returncode != 0):
        print ("An error occurred while executing the SOQL query through SFDX!  Return Code=" + str(process.returncode))
        sys.exit()

    filename = cacheDir + "/soql.csv"
    delete_file(filename)
    with open(filename, 'x') as f:
        f.write(stdout)

    return stdout


#####################################################################
## Downloads the given Quip document
#####################################################################
def get_quip_doc(accessToken, docId):
    client = quip.QuipClient(access_token=accessToken)
    user = client.get_authenticated_user()

    thread = client.get_thread(id=docId)
    return thread['html']


#####################################################################
## Search a given Quip document for a keyword
#####################################################################
def search_quip(accessToken, searchTerm, testDocId):
    client = quip.QuipClient(access_token=accessToken)
    user = client.get_authenticated_user()

    results = client.get_matching_threads(query=searchTerm, count=10, only_match_titles=False)

    print("# of matches: " + str(len(results)))

    for result in results:
        for k, v in result.items():
            print(k, v)

    thread = client.get_thread(id=testDocId)

    threadSearch = thread['html'].casefold().find(searchTerm.casefold())
    print (threadSearch)


#####################################################################
##  Load configuration from config file, stored outside of git
#####################################################################
def load_config():
    config = dict()

    # build settings file path
    homeDir = os.environ['HOME']
    settingsFilename = os.path.join(homeDir, CONFIG_FILENAME)

    if os.path.isfile(settingsFilename) == False:
        print('Settings file does not exist: ' + settingsFilename)
        sys.exit()

    print('Configuration (' + settingsFilename + "):")
    with open(settingsFilename, "r") as f:
        for line in f:
            line_clean = line.strip()
            if len(line_clean) > 0:
                tokens = line_clean.split("=", 1)
                if len(tokens) != 2:
                    print("Invalid setting!  Expected K=V and received: " + line_clean)
                    sys.exit()

                key = tokens[0].strip()
                value = tokens[1].strip()
                config[key] = value
                print (TEXT_INDENT + key + " = " + value)

    print()

    return config


#####################################################################
##  Program Entry Point
#####################################################################
main()
