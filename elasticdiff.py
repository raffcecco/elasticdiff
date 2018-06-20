import json
import requests
from auth import Authentication 
from urllib.parse import urlparse
import csv

###################################################

class Config:

    def __init__(self, file_name):
        self.config = open(file_name)
        self.json = json.loads(self.config.read())

    def get_search_terms(self):
        search_terms = self.json["searchTerms"]
        
        if search_terms == None:
            search_terms = []
        
        if self.json["searchTermsFile"] != None and self.json["searchTermsFile"] != "":
            lines = [line.rstrip('\n') for line in open(self.json["searchTermsFile"])]
            search_terms.extend(lines)
        
        return search_terms

    def set_term(self, term):
        for n in range(len(self.json["elasticQuery1"]["query"]["bool"]["should"])):
            self.json["elasticQuery1"]["query"]["bool"]["should"][n]["multi_match"]["query"] = term
        for n in range(len(self.json["elasticQuery2"]["query"]["bool"]["should"])):
            self.json["elasticQuery2"]["query"]["bool"]["should"][n]["multi_match"]["query"] = term

    def get_query1(self):
        return json.dumps(self.json["elasticQuery1"])

    def get_query2(self):
        return json.dumps(self.json["elasticQuery2"])

    def get_query1_size(self):
        return self.json["elasticQuery1"]["size"]

    def get_query2_size(self):
        return self.json["elasticQuery2"]["size"]

    def get_url1(self):
        return self.json["url1"]

    def get_url2(self):
        return self.json["url2"]

    def getDiffFile(self):
        return self.json["diffFile"]    
###################################################

class CsvWriter:

    def __init__(self, file_name, field_names):
        file = open(file_name, 'w')
        self.writer = csv.DictWriter(file, field_names)
        self.writer.writeheader()
        
        self.field_names = field_names

        self.blank_line_dict = {}
        for field in self.field_names:
            self.blank_line_dict[field] = "";
        
        self.blank_line()

    def blank_line(self):
        self.writer.writerow(self.blank_line_dict)


###################################################

def check_rfrs_equal(term, results1, results2):
    total1 = results1["hits"]["total"]
    total2 = results2["hits"]["total"]

    if total1 != total2:
        # Different counts, so obviously no match
        return False
    elif total1 == 0 and total2 == 0:
        return True
    else:
        # If counts match, check if rfrs also match
        for n in range(0, len(results1["hits"]["hits"]) - 1):
            if results1["hits"]["hits"][n]["_id"] != results2["hits"]["hits"][n]["_id"]:
                return False

    # Counts and ids all match            
    return True
    
###################################################


# For same number of results, check if same results but different order
def check_rfrs_only_order_different(results1, results2):
    # Order is already the same
    if results1 == results2:
        return False
    
    return sorted(results1) == sorted(results2)

###################################################

def get_csv_row_data(display_rows, results1, results2, arr1, arr2):
    for n in range(0, display_rows):
        try:
            desc1 = results1["hits"]["hits"][n]["_source"]["description"]
            id1 = results1["hits"]["hits"][n]["_id"]
        except IndexError as e:
            id1 = None
            arr1.append("<NONE>")
        try:
            desc2 = results2["hits"]["hits"][n]["_source"]["description"]
            id2 = results2["hits"]["hits"][n]["_id"]
        except IndexError as e:
           id2 = None
           arr2.append("<NONE>")

        if id1 != None:
            arr1.append("[%s] %s" %(id1, desc1));
        if id2 != None:
            arr2.append("[%s] %s" %(id2, desc2));

###################################################

def write_diff_csv(csv, term, display_rows, results1, results2, url1, url2):
    url1 = "URL1:" + url1;
    url2 = "URL2:" + url2;

    total1 = results1["hits"]["total"]
    total2 = results2["hits"]["total"]

    arr1 = []
    arr2 = []

    get_csv_row_data(display_rows, results1, results2, arr1, arr2)

    only_order_different = ""

    if check_rfrs_only_order_different(arr1, arr2):
        only_order_different = ", different order"

    for n in range(0, display_rows):
        desc1 = arr1[n]
        desc2 = arr2[n]

        # Don't include rows where both results are none
        if desc1 == "<NONE>" and desc2 == "<NONE>":
            continue

        # For matching rows, set 2nd to <SAME> so easy to see
        if desc1 == desc2:
            desc2 = "<SAME>"

        if n == 0:
            csv.writer.writerow({"TERM": "%s (%s, %s%s)" % (term, total1, total2, only_order_different), url1: desc1, url2: desc2})
        else:
            csv.writer.writerow({"TERM": '"', url1: desc1, url2: desc2})

    csv.blank_line()

###################################################

def process_data(config, terms,aws_auth_value1, aws_auth_value2):
    url1 = config.get_url1();
    url2 = config.get_url2();

    csv = CsvWriter(config.getDiffFile(), field_names=["TERM", "URL1:" + url1, "URL2:" + url2] )

    headers = {'Content-Type': 'application/json'}

    for term in terms:
        config.set_term(term)        
        
        response1 = requests.post(url=url1, data = config.get_query1(), headers = headers, auth = aws_auth_value1).json()        
        response2 = requests.post(url=url2, data = config.get_query2(), headers = headers, auth = aws_auth_value2).json()

        if not check_rfrs_equal(term, response1, response2):
            print("× ", end='')
            write_diff_csv(csv, term, config.get_query1_size(), response1, response2, url1, url2)
        else:
            print ("  ", end='')

        print ("'%s' (%s,%s)" %(term, response1["hits"]["total"], response2["hits"]["total"] ) )


###################################################

def start():
    config = Config("config.json")
    url1 = config.get_url1()
    url2 = config.get_url2()

    aws_auth_value1 = ""
    aws_auth_value2 = ""
    
    if ".amazonaws.com/" in url1:
        aws_auth = Authentication(es_host=urlparse(url1).netloc, region="eu-west-1", aws_type="es")
        aws_auth_value1 = aws_auth.get_auth();

    if ".amazonaws.com/" in url2:
        aws_auth = Authentication(es_host=urlparse(url2).netloc, region="eu-west-1", aws_type="es")
        aws_auth_value2 = aws_auth.get_auth();

    print("Comparing results from:\n%s\n%s\n" %(url1, url2))
    search_terms = config.get_search_terms()

    process_data(config=config, terms=search_terms, aws_auth_value1=aws_auth_value1, aws_auth_value2=aws_auth_value2)

###################################################

start()
