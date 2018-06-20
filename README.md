# elasticdiff
Elastic Search diff tool

This tool allows you to compare the results from two Elasticsearch (ES) endoints
(or the same endpoints with two different ES indexes).

Endpoints can be localhost or dev environments.

AWS access tokens will automatically be generated for dev enviroments,
but AWS CLI and appropriate access keys will need to be present.

Ouput will be CSV file that can be imported into Excel for analysis.

Usage: `$ python3 elasticdiff.py`

The tool does not have any CLI arguments, but instead uses a config.json file to define parameters.

Example config.json:
```
{
    "url1": "http://localhost:9200/mot_search_stack/_search",     // Endpoint 1.
    "url2": "http://localhost:9200/mot_search_stack2/_search",    // Endpoint 2.

    "searchTerms": ["brake", "wheel", "rust"],                    // Inline search terms.

    "searchTermsFile" : "",                                       // A file of search terms (one per line),
                                                                  // will be added to inline searchTerms.
    "diffFile": "diffs.csv",                                      // File for output CSV.

    "elasticQuery1": {                                            // Elastic search query for Endpoint 1.
      ...  
    },
   
    "elasticQuery1": {                                            // Elastic search query for Endpoint 2.
      ...    
    }
}
```
