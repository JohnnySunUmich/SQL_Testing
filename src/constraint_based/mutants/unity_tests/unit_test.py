# from ... import generate_mutants
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from mutant import generate_mutants
from pglast import parser
from pglast.stream import RawStream
import sqlvalidator

def check_duplicate(mutant_list):
    mutants = []
    for mutant_type in mutant_list:
        for mutant in mutant_list[mutant_type]:
            mutants.append(RawStream()(mutant))
    
    duplicate_list = []
    duplicate = False
    for mutant1 in mutants:
        cnt = 0
        for mutant2 in mutants:
            if mutant1 == mutant2:
                cnt = cnt + 1
            if cnt > 1:
                break
        if cnt > 1:
            duplicate_list.append(mutant1)
            duplicate = True
            continue
    
    return duplicate, list(set(duplicate_list))

def check_validity(mutant_list):
    mutants = []
    for mutant_type in mutant_list:
        for mutant in mutant_list[mutant_type]:
            mutants.append(RawStream()(mutant))
    all_valid = True 
    invalid_list = []
    for mutant in mutants:
        # There exist some issues with sqlvalidator validation checking
        try:
            parser.parse_sql(mutant)
        except:
            all_valid = False
            invalid_list.append(mutant)

    return all_valid, invalid_list

def check_include(target_mutant, mutant_list):
    contains = False
    target_mutant = RawStream()(parser.parse_sql(target_mutant))
    for mutant_type in mutant_list:
        for mutant in mutant_list[mutant_type]:
            # print(RawStream()(mutant))
            if RawStream()(mutant) == target_mutant:
                contains = True
    return contains
    
def main():
    print("Unity Testing Starts")
    files = os.listdir(".")
    test_files = list(filter(lambda x: x[-4:] == '.txt', files))
    for testcase in test_files:
        print("Testing Test Case", testcase)
        f = open(testcase, "r")
        gt = f.readline()
        mutant_list = generate_mutants(gt)
        # check if the generated mutant list contains duplicate mutants
        # duplicate = check_duplicate(mutant_list)
        # check if the generated mutants are all valid
        # all_valid = check_validity(mutant_list)
        duplicate, duplicate_list = check_duplicate(mutant_list)
        all_valid, invalid_list = check_validity(mutant_list)
        missing = False
        missing_list = []
        while True:
            mutant = f.readline().rstrip('\n')
            if not mutant:
                break
            # print(mutant)
            if check_include(mutant, mutant_list) == False:
                missing = True
                missing_list.append(mutant)
        f.close()
        if duplicate:
            print("Test", testcase[:-4], "contains duplicated mutants")
            print(duplicate_list)
        if not all_valid:
            print("Test", testcase[:-4], "contains invalid mutants")
            print(invalid_list)
        if missing:
            print("Test", testcase[:-4], "misses desired mutants")
            print(missing_list)
    print("Unity Testing Finishes")
if __name__ == "__main__":
    main()