# amr-integrator
For the integration of the DISIS system with DHIS 2

## Deployment
First, you will have to clone the repository for the integration script
```bash
$ git clone https://github.com/HISP-Uganda/amr-integrator
$ cd amr-integrator
```
In the directory for the code base are two SQL files to run on your DISIS database

1. `integrator.sql` has the additional tables to add to DISIS database

    ```bash
        $ mysql -u root -p disis_amr < ./integrator.sql
    ```
2. `data.sql` has the data used to populate those tables

    ```bash
        $ mysql -u root -p disis_amr < ./data.sql
    ```
The above steps will help you add all the facility/regional referral mappings, 
the antibiotic coding, the organisms coding, and all the indicator mapping required for the
integration to work.

In the same directory, you have a Python script `monthly_report_generator.py` that does the 
aggregation of the data to a monthly level and queues it in a data exchange middleware for submission
to DHIS 2. 

The dependencies of the script include:

    1. [requests](https://docs.python-requests.org/en/latest/)
    2. [mysql.connector](https://dev.mysql.com/doc/connector-python/en/connector-python-installation-binary.html)


Here is how to use the script
```bash
    $ python monthly_report_generator.py -h
```
This will show you this help message 

```
    A Python script that generated monthly aggregate data from DISIS system &
    submits it to DHIS 2 via a data exchange middleware
    Usage:
    $python monthly_report_generator.py [options]
    -h show this message
    -m the month for which to generate aggregate values
    -y the year for which to generate aggregate values
    -d whether to directly send values to DHIS 2 with out exchange middleware
```

An example run to generate aggregate values for the Year `2019` and Month `01` that is to say January-2019 would be:
```bash
    $ python monthly_report_generator.py -y 2019 -m 1
```

The script can used to run the backlog by passing the different year-month combinations, otherwise, it can be scheduled to run at the
start of every month to consider the previously concluded month.
