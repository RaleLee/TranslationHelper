# TranslationHelper

## Environment
python > 3.6
``` console
$ pip install googletrans==3.1.0a0
$ pip install spacy
$ python -m spacy download en_core_web_sm
$ python -m spacy download es_core_news_sm
$ python -m spacy download zh_core_web_sm
```

## Run
First, you need to split large jsonl file into smaller ones. Like this

``` console
$ split -l 2000 -d --additional-suffix=.txt -u --suffix-length=2 val_v1.1.jsonl val_v1.1_  
```

Second, use the shell script to find all txt and execute the translation

Set up clash and export the proxy port in the `trans_json.sh`.
``` console
$ sbatch trans_json.sh spanish_trans es 
```

Third, use the spacy to do sentence segmentation