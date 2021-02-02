import os.path
from pathlib import Path
from collections import defaultdict
import functools
from markov import Markov
from util import format_error
from morph import analyze,is_keyword


class Diction:
    """思考エンジンの辞書クラス。
    クラス変数:
    DICT_RANDOM -- ランダム辞書のファイル名
    DICT_PATTERN -- パターン辞書のファイル名
    スタティックメソッド:
    line2pattern(str) -- パターン辞書読み込み用のヘルパー
    pattern2line(pattern) -- パターンハッシュをパターン辞書形式に変換する
    load_random(file) -- fileからランダム辞書の読み込みを行う
    load_pattern(file) -- fileからパターン辞書の読み込みを行う
    load_template(file) -- fileからテンプレート辞書の読み込みを行う
    load_markov(file) -- fileからマルコフ辞書の読み込みを行う
    プロパティ:
    random -- ランダム辞書
    pattern -- パターン辞書
    template -- テンプレート辞書
    markov -- マルコフ辞書
    """
    DICT_DIR = os.path.join(str(Path.home()), 'unmo')#((str(Path.home()), '.unmo','dics')) を修正。
    DICT = {'random': 'dics/random.txt',
            'pattern': 'dics/pattern.txt',
            'template': 'dics/template.txt',
            'markov': 'dics/markov.dat',
            }

    def __init__(self):
        """ファイルから辞書の読み込みを行う。"""
        self._random = Diction.load_random()#ここDictionクンかも
        self._pattern = Diction.load_pattern()
        self._template = Diction.load_template()
        self._markov = Diction.load_markov(Diction.dicfile('markov'))


    def study(self, text, parts):
        """ランダム辞書、パターン辞書、テンプレート辞書をメモリに保存する。"""
        self.study_random(text)
        self.study_pattern(text, parts)
        self.study_template(parts)
        self.study_markov(parts)

    def study_markov(self, parts):
        """形態素のリストpartsを受け取り、マルコフ辞書に学習させる。"""
        self._markov.add_sentence(parts)

    def study_template(self, parts):
        """形態素のリストpartsを受け取り、
        名詞のみ'%noun%'に変更した文字列templateをself._templateに追加する。
        名詞が存在しなかった場合、または同じtemplateが存在する場合は何もしない。
        """
        template = ''
        count = 0
        for word, part in parts:
            if is_keyword(part):
                word = '%noun%'
                count += 1
            template += word

        if count > 0 and template not in self._template[count]:
            self._template[count].append(template)


    def study_random(self, text):
        """ユーザーの発言textをランダム辞書に保存する。
        すでに同じ発言があった場合は何もしない。"""
        if not text in self._random:
            self._random.append(text)

    def study_pattern(self, text, parts):
        """ユーザーの発言textを、形態素partsに基づいてパターン辞書に保存する。"""
        for word, part in parts:
            if not is_keyword(part):  # 品詞が名詞でなければ学習しない
                continue

            # 単語の重複チェック
            # 同じ単語で登録されていれば、パターンを追加する
            # 無ければ新しいパターンを作成する
            duplicated = self._find_duplicated_pattern(word)
            if duplicated and text not in duplicated['phrases']:
                duplicated['phrases'].append(text)
            else:
                self._pattern.append({'pattern': word, 'phrases': [text]})



    def save(self):
        """メモリ上の辞書をファイルに保存する。"""
        dic_markov = os.path.join(Diction.DICT_DIR, Diction.DICT['markov'])
        self._save_random()
        self._save_pattern()
        self._save_template()
        self._markov.save(dic_markov)

    def save_dictionary(dict_key):
        """
        辞書を保存するためのファイルを開くデコレータ。
        dict_key - Dictionary.DICTのキー。
        """
        def _save_dictionary(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                """辞書ファイルを開き、デコレートされた関数を実行する。
                ディレクトリが存在しない場合は新たに作成する。"""
                if not os.path.isdir(Diction.DICT_DIR):
                    os.makedirs(Diction.DICT_DIR)
                dicfile = Diction.dicfile(dict_key)
                with open(dicfile, 'w', encoding='utf-8') as f:
                    result = func(self, *args, **kwargs)
                    f.write(result)
                return result
            return wrapper
        return _save_dictionary

    @save_dictionary('template')
    def _save_template(self):
        """テンプレート辞書を保存する。"""
        lines = []
        for count, templates in self._template.items():
            for template in templates:
                lines.append('{}\t{}'.format(count, template))
        return '\n'.join(lines)

    @save_dictionary('pattern')
    def _save_pattern(self):
        """パターン辞書を保存する。"""
        lines = [Diction.pattern_to_line(p) for p in self._pattern]#pattern2line　を修正
        return '\n'.join(lines)

    @save_dictionary('random')
    def _save_random(self):
        """ランダム辞書を保存する。"""
        return '\n'.join(self.random)

    def _find_duplicated_pattern(self, word):
        """パターン辞書に名詞wordがあればパターンハッシュを、無ければNoneを返す。"""
        return next((p for p in self._pattern if p['pattern'] == word), None)

    def load_dictionary(dict_key):
        """辞書ファイルを読み込むためのデコレータ"""
        def _load_dictionary(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                """ファイルを読み込み、行ごとに分割して関数に渡す"""
                dicfile = os.path.join(Diction.DICT_DIR, Diction.DICT[dict_key])
                if not os.path.exists(dicfile):
                    return func([], *args, **kwargs)
                with open(dicfile, encoding='utf-8') as f:
                    return func(f.read().splitlines(), *args, **kwargs)
            return wrapper
        return _load_dictionary

    @staticmethod
    @load_dictionary('random')
    def load_random(lines):
        """ランダム辞書を読み込み、リストを返す。
        空である場合、['こんにちは']という一文を追加する。"""
        return lines if lines else ['こんにちは']

    @staticmethod
    @load_dictionary('pattern')
    def load_pattern(lines):
        """パターン辞書を読み込み、パターンハッシュのリストを返す。"""
        return [Diction.make_pattern(l) for l in lines]

    @staticmethod
    @load_dictionary('template')
    def load_template(lines):
        """テンプレート辞書を読み込み、ハッシュを返す。"""
        templates = defaultdict(lambda: [])
        for line in lines:
            count, template = line.split('\t')
            if count and template:
                count = int(count)
                templates[count].append(template)
        return templates

    @staticmethod
    def load_markov(filename):
        """Markovオブジェクトを生成し、filenameから読み込みを行う。"""
        markov = Markov()
        if os.path.exists(filename):
            markov.load(filename)
        return markov

            
    
    @staticmethod
    def pattern_to_line(pattern):
        """パターンのハッシュを文字列に変換する。"""
        return '{}\t{}'.format(pattern['pattern'], '|'.join(pattern['phrases']))

    @staticmethod
    def make_pattern(line):
        """文字列lineを\tで分割し、{'pattern': [0], 'phrases': [1]}の形式で返す。"""
        pattern, phrases = line.split('\t')
        if pattern and phrases:
            # return {'pattern': pattern, 'phrases': phrases}           # 2017-10-09 修正
            return {'pattern': pattern, 'phrases': phrases.split('|')} 
             # `split`メソッドの呼び出しを`PatternResponder`ではなくこちらで行うようにしました  

    """
     　　　　　　　↓居なくなってた       
    @staticmethod
    def touch_dics():
       # 辞書ファイルがなければ空のファイルを作成しあれば何もしない。
        for dic in Diction.DICT.values():
            if not os.path.exists(dic):
                open(dic, 'w').close()
    """

    @staticmethod
    def dicfile(key):
        """辞書ファイルのパスを 'DICT_DIR/DICT[key]' の形式で返す。"""
        return os.path.join(Diction.DICT_DIR, Diction.DICT[key])


    @property
    def random(self):
        """ランダム辞書"""
        return self._random

    @property
    def pattern(self):
        """パターン辞書"""
        return self._pattern

    @property
    def template(self):
        """テンプレート辞書"""
        return self._template

    @property
    def markov(self):
        """マルコフ辞書"""
        return self._markov