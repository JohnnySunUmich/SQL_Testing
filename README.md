# SQL_Testing

To run tester, instantiate a `Tester` object and call `kill` method. For example
```python
from tester import Tester
tester = Tester(schema, conf, constraint)
result = tester.kill(query1, query2)
if result != None:
    database, num_trials = result
```
On sucess, `kill` will return a tuple of `(database, num_trials)`. Otherwise, `kill` will return `None`.
The `conf` required by tester is a dictionary constains necessary infomation:
```python
conf = {
    "sizes": [5, 5, 5], # number of rows of each table in the database
    "max_trials": 50,   # maximum number of trials that the tester can try
    "ordered": False,   # if the order of rows in the output matter
    "psql": {           # psql engin config
        "dbname": postgres,
        "username": username
    }
}
```
By default, there is a yaml file describing the dictionary.

`constraint` is a dictionary parsed from 'constraints/{pid}.yml'.

## Constraint descritpion
there are three types of constraints
1. column dependence
   1. the relationship between col X and col Y
   2. there are three types of relationship
      1. `<-`: `X<-Y` means values in col X is a subset of values in col Y
      2. `>, <, =, !=`
      3. `=>`: `if-then` logic. e.g. `X='answer' => Y!=NULL` means if col X is answer than col Y is not null
      4. `^`: join relation. `X^Y` menas col X and col Y will have overlapping values

2. column value
   1. the value filled in col X have a constraint
   2. there are three operators
      1. `|`: override typing. `X|int+null` means col X can take integer or NULL
      2. `<-`: membership. `X<-[0,10]` means col X can only take values between 0 and 10 inclusively
      3. `->`: inclusion. `X->{'S8', 'iPhone'}` means col X must contain 'S8' and 'iPhone'
      
3. row dependence
   1. the value filled in row X depends on values other rows
   2.  there three functions
       1.  `inc()`
       2.  `consec()`
       3.  `unique(.,.)`

## Schema
Schema is a json file that describes the basic information of a database with the following format
```json
{
    "Problem Number": 1,
    "Table": [
        {
            "TableName": "T1",
            "PKeys": [
                {
                    "Name": "id",
                    "Type": "int"
                }
            ],
            "FKeys": [
                {
                    "FName": "pid_f",
                    "PName": "pid",
                    "PTable": 1
                }
            ],
            "Others": [
                {
                    "Name": "name",
                    "Type": "varchar"
                }
            ]
        }
    ]
}
```
   
