from os import getcwd, sep, path
import csv

def get_id_dict(data_path, type_):
    file_path = data_path + type_ + '.csv'
    with open(file_path, 'r') as id_file:
        elements = dict(csv.reader(id_file, delimiter=','))
    return elements

def store_id_dict(data_path, type_, id_dict):
    file_path = data_path + type_ + '.csv'
    with open(file_path, 'w') as id_file:
        for key in id_dict:
            id_file.write(f"{key},{id_dict[key]}\n")