import sys
import quip
import os
import subprocess

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

    quipAccessToken = config[CONFIG_KEY_QUIP_ACCESS_TOKEN].strip()

    results = sfdc_query(config)
    header = results[0]
    del results[0]

    outputHeader = header.split(",")
    outputHeader = outputHeader + searchTerms
    output = [ outputHeader ]

    for line in results:
        l = line.strip()
        if (len(l) > 0):
            csv = l.split(',')

            accountId = csv[0].strip()
            accountName = csv[1].strip()
            accountSubRegion = csv[2].strip()
            accountPlanUrl = csv[3].strip()
            csPlanUrl = csv[4].strip()

            process_account(output, quipAccessToken, config[CONFIG_KEY_QUIP_URL_STRIP].strip(), accountId, accountName, accountSubRegion, accountPlanUrl, csPlanUrl, searchTerms)

    print ("Number of lines: " + str(len(output)))
    for line in output:
        columnPrint = ",".join(line)
        print(columnPrint)


#####################################################################
## Process account record
#####################################################################
def process_account(output, accessToken, quipUrlStrip, accountId, accountName, accountSubRegion, accountPlanUrl, csPlanUrl, searchTerms):
    matches = 0

#    for searchTerm in searchTerms:
#        search_quip(config[CONFIG_KEY_QUIP_ACCESS_TOKEN], searchTerm, config["TEST_DOC_ID"].casefold())

    if (len(csPlanUrl) > 0):
        u = csPlanUrl.replace(quipUrlStrip, "")
        t = u.split("/", 1)
        if (len(t) > 1):
            docId = t[0]
        else:
            docId = u
        print ("Doc ID = " + docId)
        #csPlan = get_quip_doc(accessToken, docId)


#    threadSearch = thread['html'].casefold().find(searchTerm.casefold())


#####################################################################
## Query SFDC for a list of Quip Documents to search
#####################################################################
def sfdc_query(config):

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

    lines = stdout.splitlines()
    
    return lines


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
