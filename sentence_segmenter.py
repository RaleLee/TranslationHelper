import os
import subprocess
import json
import re
from tqdm import tqdm
from spacy.lang.es import Spanish
from spacy.lang.ru import Russian
from spacy.lang.en import English

langs = ['es', 'ru', 'en']
sentencizers = {'es': Spanish(), 'ru': Russian(), 'en': English()}
file_type = ['train', 'val', 'test']
regex_url = r'({\"smallUrl[^}]*})'


def read_file(path: str):
    f = open(path, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    return lines


def pair_json(prefix: str, src: str, tgt: str):
    for file in file_type:
        src_lines = read_file(prefix + file + '.src.' + src)
        src_oracle_lines = read_file(prefix + file + '.src.' + tgt)
        tgt_lines = read_file(prefix + file + '.tgt.' + tgt)
        assert len(src_lines) == len(tgt_lines)
        assert len(src_lines) == len(src_oracle_lines)

        with open(prefix + file + '.jsonl', 'w', encoding='utf-8') as f:
            for sl, sol, tl in zip(src_lines, src_oracle_lines, tgt_lines):
                line = {'doc': sl.strip(), 'oracle': sol.strip(), 'summary': tl.strip()}
                f.write(json.dumps(line, ensure_ascii=False) + '\n')


def seg_and_align(prefix: str, src: str, tgt: str, old_ver: str, new_ver: str):
    src_seger, tgt_seger = sentencizers[src], sentencizers[tgt]
    src_seger.add_pipe('sentencizer')
    tgt_seger.add_pipe('sentencizer')

    def split_smallUrl_and_seg(s: str, seger):
        lst = re.split(regex_url, s)
        ret = []
        for ls in lst:
            if re.search(regex_url, ls) is None:
                seg_ls = seger(ls.strip())
                ret.extend([t.text.strip() for t in seg_ls.sents])
            else:
                ret.append(ls.strip())
        return ret

    for file in file_type:
        json_lines = read_file(prefix + file + old_ver + '.jsonl')

        with open(prefix + file + new_ver + '.jsonl', 'w', encoding='utf8') as fo:
            suc, allen = 0, len(json_lines)
            for json_line in tqdm(json_lines, ncols=50):
                line = json.loads(json_line.strip())
                src_seg_list = split_smallUrl_and_seg(line['doc'], src_seger)
                oracle_seg_list = split_smallUrl_and_seg(line['oracle'], tgt_seger)
                if len(src_seg_list) == len(oracle_seg_list):
                    suc += 1
                line['doc_seg_list'], line['oracle_seg_list'] = src_seg_list, oracle_seg_list
                fo.write(json.dumps(line, ensure_ascii=False) + '\n')
            print(f'{suc/ allen * 100: .2f}')


def hunalign_wrapper(prefix: str, old_ver: str, new_ver: str):
    def write_tmp_file(tmp_path: str, sens: list):
        with open(tmp_path, 'w', encoding='utf-8') as tf:
            for sen in sens:
                tf.write(sen + '\n')

    def read_align_file(align_path: str):
        af = open(align_path, 'r', encoding='utf-8')
        ladders = af.readlines()
        af.close()

        ret = []
        for ladder in ladders:
            s, t, cf = ladder.strip().split()
            mid = (s, t, cf)
            ret.append(mid)
        return ret

    for file in file_type:
        json_lines = read_file(prefix + file + old_ver + '.jsonl')

        with open(prefix + file + new_ver + '.jsonl', 'w', encoding='utf8') as fo:
            for json_line in tqdm(json_lines, ncols=50):
                line = json.loads(json_line.strip())
                src_tmp_path, oracle_tmp_path, ladder_tmp_path = 'src_tmp.txt', 'oracle_tmp.txt', 'align_tmp.txt'
                write_tmp_file(src_tmp_path, line['doc_seg_list'])
                write_tmp_file(oracle_tmp_path, line['oracle_seg_list'])

                # hunalign
                child = subprocess.Popen(f'~/hunalign-1.1/src/hunalign/hunalign -utf null.dic '
                                         f'{src_tmp_path} {oracle_tmp_path} > {ladder_tmp_path}', shell=True)
                child.wait()
                alignments = read_align_file(ladder_tmp_path)
                line['doc_oracle_align'] = alignments
                fo.write(json.dumps(line, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    # pair src src_oracle_trans tgt into a jsonl
    pair_json('spanish/', 'es', 'en')
    # seg and align
    seg_and_align('spanish/', 'es', 'en', '', '_v1.0')
    # hunalign
    hunalign_wrapper('spanish/', '_v0.1', '_v0.2')
    # hunalign_wrapper('spanish/', '_v1.0', '_v1.1')
