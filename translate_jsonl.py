import argparse
import json
import re
from googletrans import Translator
from tqdm import tqdm

translator = Translator()
parser = argparse.ArgumentParser()
parser.add_argument('--language', '-l', type=str)
parser.add_argument('--filepath', '-f', type=str)
args = parser.parse_args()
regex_url = r'({\"smallUrl[^}]*})'


def read_file(path: str):
    f = open(path, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    return lines


def trans_jsonl(la: str, file_path: str):
    json_lines = read_file(file_path)
    src_lang = la if la != 'zh' else 'zh-cn'

    # remove url and split into tuple with url T/F
    def split_smallUrl(s: str):
        lst = re.split(regex_url, s)
        ret = []
        for ls in lst:
            if re.search(regex_url, ls) is None:
                ret.append((ls.strip(), True))
            else:
                ret.append((ls.strip(), False))
        return ret

    retry_utt, retry_cnt = [], 0
    with open(file_path + '.suc', 'w', encoding='utf-8') as fo:
        for json_line in tqdm(json_lines, ncols=50):
            line = json.loads(json_line.strip())
            src_list = split_smallUrl(line['doc'])
            try:
                trans_list, suc = [], True
                for sl, not_Url in src_list:
                    if not_Url:
                        res = translator.translate(sl, src=src_lang, dest='en').text
                        if res != sl:
                            trans_list.append(res)
                        else:
                            suc = False
                    else:
                        trans_list.append(sl)
                if suc:
                    line['google_trans'] = ' '.join(trans_list) if len(trans_list) > 1 else trans_list[0]
                    assert line['google_trans'] != line['doc']
                    fo.write(json.dumps(line, ensure_ascii=False) + '\n')
                else:
                    retry_utt.append((line, src_list))
            except:
                retry_utt.append((line, src_list))
        while len(retry_utt) > 0 and retry_cnt < 4:
            rere = []
            for lin, src_li in retry_utt:
                try:
                    trans_list, suc = [], True
                    for sl, not_Url in src_li:
                        if not_Url:
                            res = translator.translate(sl, src=src_lang, dest='en').text
                            if res != sl:
                                trans_list.append(res)
                            else:
                                suc = False
                        else:
                            trans_list.append(sl)
                    if suc:
                        lin['google_trans'] = ' '.join(trans_list) if len(trans_list) > 1 else trans_list[0]
                        fo.write(json.dumps(lin, ensure_ascii=False) + '\n')
                    else:
                        rere.append((lin, src_li))
                except:
                    rere.append((lin, src_li))
            retry_utt = rere
            retry_cnt += 1
    if len(retry_utt) > 0:
        with open(file_path+'.fail', 'w', encoding='utf-8') as ff:
            for ru, _ in retry_utt:
                ff.write(json.dumps(ru, ensure_ascii=False) + '\n')
    print(f'{file_path} failed: {len(retry_utt)}')
    return


if __name__ == '__main__':
    trans_jsonl(args.language, args.filepath)
