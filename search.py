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
CONFIG_KEY_SFDC_USERNAME = "SFDC_USERNAME"
CONFIG_KEY_SFDC_QUERY = "SFDC_QUERY"


#####################################################################
## Main Logic
#####################################################################
def main():
    print("search.py")
    print()

    numArguments = len(sys.argv)
    if numArguments <= 1:
        print ("Usage: search.py <search_term> .......")
        print ("<search_term> can be repeated to incorporate searching on as many terms as desired")
        sys.exit()

    searchTerms = sys.argv
    del searchTerms[0]
    print ("Search Terms:")
    for searchTerm in searchTerms:
        print(TEXT_INDENT + searchTerm)
    print()

    config = load_config()

    results = sfdc_query(config)
    for line in results:
        print(line)

#    for searchTerm in searchTerms:
#        search_quip(config[CONFIG_KEY_QUIP_ACCESS_TOKEN], searchTerm, config["TEST_DOC_ID"].casefold())


#####################################################################
## Query SFDC for a list of Quip Documents to search
#####################################################################
def sfdc_query(config):

    print ("Executing SOQL query to search for Quip documents now using SFDX...  Expecting that you have already authenticated prior to running this script.")
    command = [
        "sfdx",
        "data:soql:query",
        "-q",
        config[CONFIG_KEY_SFDC_QUERY].casefold(),
        "-o",
        config[CONFIG_KEY_SFDC_USERNAME].casefold(),
        "-r",
        "csv"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderrr = process.communicate()
    if (process.returncode != 0):
        print ("An error occurred while executing the SOQL query through SFDX!  Return Code=" + str(process.returncode))
        sys.exit()

    lines = stdout.splitlines()
    del lines[0]
    
    return lines


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

main()
