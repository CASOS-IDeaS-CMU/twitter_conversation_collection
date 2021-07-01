import os 
import json
import gzip
import response_status_code
from datetime import datetime 

'''
Read ids one by one into file as long
'''
def read_lines_into_file(filename):
    with open(filename, 'r') as f:
        content = f.readlines()

    errorlines = []
    final_content = []
    for x in content: 
        try:
            final_content.append(int(x.strip()))
        except:
            errorlines.append(x)
    return final_content, errorlines

def write_array_to_file(array_to_write, outdir, label_string='error users'):
    out_filename = os.path.join(outdir, f'{label_string}.txt')
    with open(out_filename, 'w') as of:
        for u in array_to_write:
            of.write(f'{u}\n')
    of.close()

def read_json_file(json_filename):
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            return json.loads(f.read()), response_status_code.INTERNAL_OK
    except:
        return None, response_status_code.INTERNAL_JSON_FILE_ERROR

'''
Write Twitter V2 API response json to gzip
'''
def write_response_json_to_gzip(response_json, outfilename):
    with gzip.open(outfilename, 'wb') as f:
        line = json.dumps(response_json)
        f.write(line.encode())
    f.close()
    return 

def write_response_arr_to_gzip(response_array, outfilename):
    with gzip.open(outfilename, 'wb') as f:
        print('response array ', len(response_array))
        for a in response_array:
            print(a)
            line = json.dumps(a)
            f.write(line.encode())
    f.close()
    return 

def read_gzip_json_file(gzipfilename):
    input_data = []
    try:
        for line in gzip.open(gzipfilename, 'r'): 
            input_data.append(json.loads(line))
        full_dict = input_data[0]
        return full_dict, response_status_code.INTERNAL_OK
    except:
        return None, response_status_code.INTERNAL_GZIP_FILE_ERROR

def make_results_dir(outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_result_dir = os.path.join(outdir, f'results_{now_str}')
    os.makedirs(final_result_dir)

    return final_result_dir