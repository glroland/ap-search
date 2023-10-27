import sys
import csv
import os
from datetime import datetime
from datetime import date


#####################################################################
## Constants
#####################################################################


#####################################################################
## Main Logic
#####################################################################
def main():
    print("revreport.py")
    print()

    print ("Usage: revreport.py <input> <mappingfile> <prodoutput> <summaryoutput>")
    print ("<input> is the export details report that includes the detailed results from system of record")
    print ("<mappingfile> provides translations for one account name to another")
    print ("<prodoutput> is the summarized revenue analysis with product level detail")
    print ("<summaryoutput> is the summarized revenue analysis simplified at the account level")
    print ()

    # validate arguments
    if (len(sys.argv) != 5):
        print ("Insufficient Arguments!")
        sys.exit()

    # pull config from command line
    inputFilename = sys.argv[1]
    mappingFilename = sys.argv[2]
    prodOutputFilename = sys.argv[3]
    summaryOutputFilename = sys.argv[4]
    print ("Input File: " + inputFilename)
    print ("Mapping File: " + mappingFilename)
    print ("Output File for Product Level Revenue: " + prodOutputFilename)
    print ("Output File for Revenue Summary Report: " + summaryOutputFilename)
    print ()

    # Load mapping file
    mappings = loadMapping(mappingFilename)
    print()

    # Load input file and extract key data elements
    detail = loadDetailFromInputFile(inputFilename, mappings)
    print()

    # Generate detail report
    productLevelReportDetail = generateProductLevelReport(prodOutputFilename, detail)
    print ()

    # Generate account summary report
    accountSummaryReport = generateSummaryReport(summaryOutputFilename, productLevelReportDetail)
    print ()

    # All done
    print ("Complete!")
    print ()


#####################################################################
##  Generate Account Summary Report based on Product Level Revenue
#####################################################################
def generateProductLevelReport(outputFile, detail):
    print ("Generating Product Level Revenue Report...")

    results = []

    for detailRecord in detail:
        # does record exist in results?
        summaryRecord = None
        for r in results:
            if (r["accountOwner"] == detailRecord["accountOwner"]) and (r["accountName"] == detailRecord["accountName"]) and (r["productLine"] == detailRecord["productLine"]):
#            if (r["accountName"] == detailRecord["accountName"]) and (r["productLine"] == detailRecord["productLine"]):
                if summaryRecord != None:
                    print ("ERROR> Multiple Summary Records found in result set!")
                    sys.exit()
                summaryRecord = r
        if summaryRecord == None:
            customerName = detailRecord["accountName"]
#            if len(detailRecord["knownAs"].strip()) > 0:
#                customerName = detailRecord["knownAs"].strip()
            if len(detailRecord["ultimateAccountName"].strip()) > 0:
                customerName = detailRecord["ultimateAccountName"].strip()
            summaryRecord = {
                "pod": detailRecord["pod"],
                "accountOwner": detailRecord["accountOwner"],
                "accountName": detailRecord["accountName"],
#                "ultimateAccountName": detailRecord["ultimateAccountName"],
#                "accountName": customerName,
                "productFamily": detailRecord["productFamily"],
                "productLine": detailRecord["productLine"],
                "2016": 0.0,
                "2017": 0.0,
                "2018": 0.0,
                "2019": 0.0,
                "2020": 0.0,
                "2021": 0.0,
                "2022": 0.0,
                "2023": 0.0
            }
            results.append(summaryRecord)

        # update yearly revenue values
        summaryRecord["2016"] = summaryRecord["2016"] + calculateRevenueForYear(2016, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2017"] = summaryRecord["2017"] + calculateRevenueForYear(2017, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2018"] = summaryRecord["2018"] + calculateRevenueForYear(2018, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2019"] = summaryRecord["2019"] + calculateRevenueForYear(2019, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2020"] = summaryRecord["2020"] + calculateRevenueForYear(2020, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2021"] = summaryRecord["2021"] + calculateRevenueForYear(2021, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2022"] = summaryRecord["2022"] + calculateRevenueForYear(2022, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])
        summaryRecord["2023"] = summaryRecord["2023"] + calculateRevenueForYear(2023, detailRecord["amount"], detailRecord["startDate"], detailRecord["endDate"])

    print (str(len(results)) + " records are in the resulting product level report.")

    print ("Writing data to file: " + outputFile)
    if os.path.exists(outputFile):
        os.remove(outputFile)
    f = open(outputFile, "w")
    for r in results:
        f.write("\"" + r["pod"] + "\",\"" + r["accountOwner"] + "\",\"" +  r["accountName"] + "\",\"" + r["productFamily"] + "\",\"" + r["productLine"] + "\"," + str(r["2016"]) + "," + str(r["2017"]) + "," + str(r["2018"]) + "," + str(r["2019"]) + "," + str(r["2020"]) + "," + str(r["2021"]) + "," + str(r["2022"]) + "," + str(r["2023"]) + "\n")
#        f.write("\"" + r["pod"] + "\",\"" + r["accountOwner"] + "\",\"" +  r["customerName"] + "\",\"" +  r["ultimateAccountName"] + "\",\"" +  r["accountName"] + "\",\"" + r["productFamily"] + "\",\"" + r["productLine"] + "\"," + str(r["2016"]) + "," + str(r["2017"]) + "," + str(r["2018"]) + "," + str(r["2019"]) + "," + str(r["2020"]) + "," + str(r["2021"]) + "," + str(r["2022"]) + "," + str(r["2023"]) + "\n")

    return results


#####################################################################
##  Calculate revenue by year
#####################################################################
def calculateRevenueForYear(year, amount, startDate, endDate):
    days = (endDate - startDate).days + 1
    revPerDay = amount / days

    yearStart = date(year, 1, 1)
    yearEnd = date(year, 12, 31)

    rev = 0.0
    if startDate > yearEnd:
        rev = 0.0
    elif endDate < yearStart:
        rev = 0.0
    elif (startDate <= yearStart) and (endDate >= yearEnd):
        rev = ((yearEnd - yearStart).days + 1) * revPerDay
    else:
        if startDate > yearStart:
            yearStart = startDate
        if endDate < yearEnd:
            yearEnd = endDate
        rev = ((yearEnd - yearStart).days + 1) * revPerDay

    # truncate precision to pennies
    rev = float('{:.2f}'.format(rev))

    return rev


#####################################################################
##  Generate Account Summary Report based on Product Level Revenue
#####################################################################
def generateSummaryReport(outputFile, productLevelReportDetail):
    print ("Generating Account Summary Report...")

    results = []

    for detailRecord in productLevelReportDetail:
        # does record exist in results?
        summaryRecord = None
        for r in results:
            if (r["accountOwner"] == detailRecord["accountOwner"]) and (r["accountName"] == detailRecord["accountName"]):
#            if (r["accountName"] == detailRecord["accountName"]):
                if summaryRecord != None:
                    print ("ERROR> Multiple Summary Records found in result set!")
                    sys.exit()
                summaryRecord = r
        if summaryRecord == None:
            summaryRecord = {
                "pod": detailRecord["pod"],
                "accountOwner": detailRecord["accountOwner"],
                "accountName": detailRecord["accountName"],
                "2016": 0.0,
                "2017": 0.0,
                "2018": 0.0,
                "2019": 0.0,
                "2020": 0.0,
                "2021": 0.0,
                "2022": 0.0,
                "2023": 0.0
            }
            results.append(summaryRecord)

        # update yearly revenue values
        summaryRecord["2016"] = summaryRecord["2016"] + detailRecord["2016"]
        summaryRecord["2017"] = summaryRecord["2017"] + detailRecord["2017"]
        summaryRecord["2018"] = summaryRecord["2018"] + detailRecord["2018"]
        summaryRecord["2019"] = summaryRecord["2019"] + detailRecord["2019"]
        summaryRecord["2020"] = summaryRecord["2020"] + detailRecord["2020"]
        summaryRecord["2021"] = summaryRecord["2021"] + detailRecord["2021"]
        summaryRecord["2022"] = summaryRecord["2022"] + detailRecord["2022"]
        summaryRecord["2023"] = summaryRecord["2023"] + detailRecord["2023"]

    print (str(len(results)) + " records are in the resulting product level report.")

    print ("Writing data to file: " + outputFile)
    if os.path.exists(outputFile):
        os.remove(outputFile)
    f = open(outputFile, "w")
    for r in results:
        f.write("\"" + r["pod"] + "\",\"" + r["accountOwner"] + "\",\"" +  r["accountName"] + "\"," + str(r["2016"]) + "," + str(r["2017"]) + "," + str(r["2018"]) + "," + str(r["2019"]) + "," + str(r["2020"]) + "," + str(r["2021"]) + "," + str(r["2022"]) + "," + str(r["2023"]) + "\n")

    return results


#####################################################################
##  Loads the account name translation/mapping file
#####################################################################
def loadMapping(mappingFilename):
    print ("Loading account name mapping file...")

    mappings = []
    numRows = 0
    f = open(mappingFilename, "r")
    line = f.readline()
    while line:
        csvLine = list(csv.reader([line]))[0]
        if len(csvLine) >= 2:
            numRows += 1
            record = {
                "from": csvLine[0],
                "to": csvLine[1]
            }

            mappings.append(record)

        line = f.readline()
    
    print (str(numRows) + " rows read from mapping file.")

    return mappings


#####################################################################
##  Parse input file and extrapolate key data elements
#####################################################################
def loadDetailFromInputFile(inputFilename, mappings):
    print ("Extrapolating detail from input file...")

    results = []

    numRows = 0
    f = open(inputFilename, "r")
    line = f.readline()
    while line:
        csvLine = list(csv.reader([line]))[0]
        if len(csvLine) >= 40:
            if csvLine[0] != "Opportunity ID - 18 Digit":
                numRows += 1
                record = {
                    "pod": csvLine[38],
                    "accountOwner": csvLine[37],
                    "individualAccountName": csvLine[39],
                    "ultimateAccountName": csvLine[36],
                    "accountNameAccountName": csvLine[40],
                    "knownAs": csvLine[38],
                    "accountName": csvLine[36],
                    "productLine": csvLine[32],
                    "productFamily": csvLine[33],
                    "startDate": datetime.strptime(csvLine[15], '%m/%d/%Y').date(),
                    "endDate": datetime.strptime(csvLine[16], '%m/%d/%Y').date(),
                    "amount": float(csvLine[23])
                }
                if len(record["accountName"].strip()) == 0:
                    record["accountName"] = record["individualAccountName"]
                if len(record["accountName"].strip()) == 0:
                    record["accountName"] = record["ultimateAccountName"]
                if len(record["accountName"].strip()) == 0:
                    record["accountName"] = record["accountNameAccountName"]
                if len(record["accountName"].strip()) == 0:
                    record["accountName"] = record["knownAs"]

                if len(record["accountName"].strip()) == 0:
                    print(record)
                    print(csvLine)
                    print()
                else:
                    for mapping in mappings:
                        if record["accountName"].strip().upper() == mapping["from"].strip().upper():
                            record["accountName"] = mapping["to"].strip()
            
                results.append(record)

        line = f.readline()
    
    print (str(numRows) + " rows read from input file.")

    return results


#####################################################################
##  Program Entry Point
#####################################################################
main()

