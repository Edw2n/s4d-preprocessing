from PIL import Image
import pickle
import argparse
import os
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('config', help="config file")
args = parser.parse_args()

m = __import__(args.config.split('.')[0], fromlist=['target_dir', 'LOG_FILE_NAME', 'PARAM_TOTAL_NUM', 'OPTION', 'VALID_LENGTH'])
exceptions_info = {}

TAKEN_FOLDER = f'{m.target_dir}/taken{"_" if len(m.OPTION) > 0 else ""}{m.OPTION}'
LODED_FOLDER = f'{m.target_dir}/loaded'
Path(TAKEN_FOLDER).mkdir(parents=True, exist_ok=True)


def get_missed_imgpath(param_num, log):
    estimated_taken_path = None

    print('missed param_num:', param_num, log[param_num])
    if param_num>1:
        before_log = log[param_num-1]
        before_folder = before_log['camera_folder']
        before_img = before_log['img_name']
    else:
        print('## see previous dped path log')
        return estimated_taken_path
    if param_num < m.PARAM_TOTAL_NUM:
        after_log = log[param_num+1]
        after_folder = after_log['camera_folder']
        after_img = after_log['img_name']
    else:
        print('## see next dped path log')
        return estimated_taken_path
    
    if after_folder == before_folder:
        print('## before/after folders are same')
        print(f'#### before: {before_folder}/{before_img}, after: {after_folder}/{after_img}')
        estimated_img_gap = int(after_img[4:-4]) - int(before_img[4:-4])
        if estimated_img_gap ==2:
            estimated_img = before_img[:4] + f'{int(before_img[4:-4]) + 1:04}' + before_img[-4:]
            print('##### Img number diff between Before and After is 2')
            estimated_taken_path = f'{after_folder}/{estimated_img}'
            print(f'##### estimated img path: {estimated_taken_path}')
        else:
            print('##### exception: but before and after is not diff 2')
    elif after_folder>before_folder:
        print('##  before/after folders are different')
        print(f'#### before: {before_folder}/{before_img}, after: {after_folder}/{after_img}')
        if int(after_img[4:-4])==2:
            estimated_img = after_img[:4] + f'{int(after_img[4:-4]) - 1:04}' + after_img[-4:]
            estimated_taken_path = f'{after_folder}/{estimated_img}'
            print(f'##### estimated img path: {estimated_taken_path}')
        elif int(after_img[4:-4])==1:
            estimated_img = before_img[:4] + f'{int(before_img[4:-4]) + 1:04}' + before_img[-4:]
            estimated_taken_path = f'{before_folder}/{estimated_img}'
            print(f'##### estimated img path: {estimated_taken_path}')
        else:
            print(int(after_img[4:-4]))
            print('#### excpetion: after_img is not 0002')
    else:
        print('### excpetion: after_folder<before_folder')
    
    return estimated_taken_path

def unify_taken(data):
    prev_log = None
    exceptions_info = {}
    for dped_path, options_log in list(data.items())[:m.VALID_LENGTH]:
        for param_num,  taken_log in options_log.items():
            img_name = taken_log['img_name']
            folder_name = taken_log['camera_folder']
            if 'CANON' not in folder_name or '.JPG' not in img_name:
                exceptions_info.setdefault(dped_path, {
                    'options_log':options_log,
                    'exceptions_params':[],
                    'prev_log': prev_log
                    })['exceptions_params'].append(param_num)  # returns None!
            else:
                taken_path = f'{LODED_FOLDER}/{folder_name}/{img_name}'
                dst = f'{TAKEN_FOLDER}/{folder_name[:-5]}_{img_name}'
                shutil.copyfile(taken_path, dst)
                taken_log['taken_path'] = dst
        prev_log = options_log
    print(exceptions_info.keys())
    return exceptions_info

with open(f'{LODED_FOLDER}/{m.LOG_FILE_NAME}', 'rb') as f:
    data = pickle.load(f)

    m.VALID_LENGTH = m.VALID_LENGTH if m.VALID_LENGTH > 0 else len(data)
    print('valid length', m.VALID_LENGTH)

    prev_log = None
    
    #record exceptions
    exceptions_info = unify_taken(data)
    
    # exception 이 연속이면 어카지?
    # delay로 처리 => 이건 delay해당하는거 나오면 그때 추가합시다요

    # print(exceptions_info)
    remove_list = [
    ]

    delayed = [
        # start end missed (end 포함) (shift)
            # start -1 <- start
            # end-1 <- end
            # end <- missed
   
    ]

    to_be_filled = [
      
    ]

    for dped_path, log in exceptions_info.items():
        
        # if dped_path in remove_list: # 왜 필요한지 이따 체크
        #     continue
        for param_num in list(log['exceptions_params']):
            estimated_taken_path = get_missed_imgpath(param_num, log['options_log'])
            print(estimated_taken_path)
            if estimated_taken_path:
                # 사용자 입력받아서 체크 후 전처리
                while True:
                    print('dped:', dped_path)
                    print('curr log:', list(map( lambda x: x['camera_folder']+'/'+x['img_name'],log['options_log'].values())))
                    print('prev log:', list(map( lambda x: x['camera_folder']+'/'+x['img_name'],log['prev_log'].values())))
                    user_input = input(f'##### copy missed image({estimated_taken_path}) to taken? (please take one of y/n/rm).')
                    
                    if user_input == 'y':
                        folder_name, img_name = estimated_taken_path.split('/')
                        taken_path = f'{LODED_FOLDER}/{folder_name}/{img_name}'
                        dst = f'{TAKEN_FOLDER}/{folder_name[:-5]}_{img_name}'
                        shutil.copyfile(taken_path, dst)            
                        print(f'{estimated_taken_path} is copied in taken iamge folder ({TAKEN_FOLDER})')
                        
                        # taken log 수정 하고 저장하기 새거로
                        original_log = log['options_log'][param_num]
                        original_log['img_name'] = img_name
                        original_log['camera_folder'] = folder_name
                        log['exceptions_params'].remove(param_num)

                        original_log['taken_path'] = dst

                        print(data[dped_path][param_num])
                        break
                    elif user_input == 'n':
                        print('nothing is copied')
                        break
                    elif user_input == 'rm':
                        print(f'takens for target image {dped_path} will be removed') # curr : 첫, 끝, deped 이미지가 같고, missing 맞고, 첫 -1, 끝 +1이 curr 와 다르면
                        remove_list.append(dped_path)
                        break
                    else:
                        print('Please enter character among (y/n/rm).')
            else:
                print('exception!!!')
                print('dped:', dped_path)
                print('exception params:', param_num)
                print('curr log:', list(map( lambda x: x['camera_folder']+'/'+x['img_name'],log['options_log'].values())))
                print('prev log:', list(map( lambda x: x['camera_folder']+'/'+x['img_name'],log['prev_log'].values())))
                user_input = input(f'##### exception  to taken? (please take one of y/n/rm).')
                
    keys = list(data.keys())
    UPDATED_LOG_FILE_NAME = f"{m.LOG_FILE_NAME[:-7]}_restored.pickle"
    with open(f'{TAKEN_FOLDER}/{UPDATED_LOG_FILE_NAME}', "wb") as f_ub:
        updated_log = dict(list(data.items())[:m.VALID_LENGTH])
        for key in remove_list:
            del updated_log[key]

        # map(lambda key_path: updated_log.pop(key_path) and exceptions_info.pop(key_path), remove_list)
        pickle.dump(updated_log, f_ub) # data를 다 덤프뜨면 안됨. valid만 떠야함.
        print(f'updated log is saved in {TAKEN_FOLDER}/{UPDATED_LOG_FILE_NAME}') 
        
        cnt = 0
        not_solved_dp = 0
        for dped_path, log in data.items():
            # print(exceptions_info.keys())
            if dped_path in exceptions_info:
                exception_log = exceptions_info[dped_path] 
                not_solved = exception_log['exceptions_params']
                if len(not_solved)>0:
                    print(f'dped: {dped_path},', list(map( lambda x: x['camera_folder']+'/'+x['img_name'],log.values())) )
                    print(f'##not solved params: {not_solved}')
                    idx = keys.index(dped_path)
                    next_key = keys[idx+1]
                    cnt +=len(not_solved)
                    not_solved_dp +=1
                if dped_path in remove_list:
                    print(f'takens for {dped_path} are removed')

        print(f'Total {cnt} logs are not solved')
        print(f'Total {len(remove_list)} log sets are removed')
        print(f'Total {len(updated_log)} among {m.VALID_LENGTH} are perfects(full params logged)')

    # mkdir takens => cropped => ~~
    # cp each imgs to taken (format: "foldernum_imgnum.jpg" )
    # mv missed img
    
   