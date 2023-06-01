import sys
import quip
import os

#####################################################################
## Constants
#####################################################################
TEXT_INDENT = " - "
CONFIG_FILENAME = ".search.py.settings"
CONFIG_KEY_QUIP_ACCESS_TOKEN = "QUIP_ACCESS_TOKEN"


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

    for searchTerm in searchTerms:
        search_quip(config[CONFIG_KEY_QUIP_ACCESS_TOKEN], searchTerm)



#####################################################################
## Search a given Quip document for a keyword
#####################################################################
def search_quip(accessToken, searchTerm):
    client = quip.QuipClient(access_token=accessToken)
    user = client.get_authenticated_user()

    results = client.get_matching_threads(query=searchTerm, count=10, only_match_titles=False)

    print("# of matches: " + str(len(results)))

    for result in results:
        for k, v in result.items():
            print(k, v)

    thread = client.get_thread(id="ab")

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
