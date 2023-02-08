from itertools import permutations
from collections import Counter

def dif_table(data1, data2, consider_order=False):
    # return True if data1 is different from data2
    if len(data1) == 0 and len(data2) == 0:
        return False
    def generate_permutation_datas(data):
        result = []
        if len(data) == 0:
            return []
        data_permutations = []
        for i in data:
            row_permutation = list(permutations(i))
            data_permutations.append(row_permutation)
        row_permutation_len = len(data_permutations[0])
        for i in range(row_permutation_len):
            new_permutation_table = []
            for row in data_permutations:
                new_permutation_table.append(row[i])
            result.append(new_permutation_table)
        return result

    if len(data1) != len(data2):
        return True
    data2_permutations = generate_permutation_datas(data2)

    if consider_order:
        for d2 in data2_permutations:
            if d2 == data1:
                return False
    else:
        bag_semantic_data1 = dict(Counter(data1))
        for d2 in data2_permutations:
            bag_semantic_data2 = dict(Counter(d2))
            if bag_semantic_data1 == bag_semantic_data2:
                return False
    return True