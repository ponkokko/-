
from random import choice, randrange
from janome.tokenizer import Tokenizer
from responder import RandomResponder,WhatResponder,PatternResponder, TemplateResponder, MarkovResponder
from dictionary import Diction
from morph import analyze

class Unmo:
    """人工無脳コアクラス。

    プロパティ:
    name -- 人工無脳コアの名前
    responder_name -- 現在の応答クラスの名前
    """

    def __init__(self,name):
        """文字列を受け取り、コアインスタンスの名前に設定する。
        Responder(What, Random, Pattern)インスタンスを作成し、保持する。
        Dictionaryインスタンスを作成し、保持する。
        Tokenizerインスタンスを作成し、保持する。
        """
        self._tokenizer = Tokenizer()
        self._dictionary = Diction()

        self._responders = {
            'what':     WhatResponder('What',self._dictionary),
            'random':   RandomResponder('Random',self._dictionary),
            'pattern': PatternResponder('Pattern', self._dictionary),
            'template': TemplateResponder('Template', self._dictionary),
            'markov':   MarkovResponder('Markov', self._dictionary),
        }
        self._name = name
        self._responder = self._responders['pattern']

    
    def dialogue(self, text):
        """ユーザーからの入力を受け取り、Responderに処理させた結果を返す。
        呼び出されるたびにランダムでResponderを切り替える。
        入力をDictionaryに学習させる。"""
        chance = randrange(0, 100)
        if chance in range(0, 29):
            self._responder = self._responders['pattern']
        elif chance in range(30, 49):
            self._responder = self._responders['template']
        elif chance in range(50, 69):
            self._responder = self._responders['random']
        elif chance in range(70, 89):
            self._responder = self._responders['markov']
        else:
            self._responder = self._responders['what']

        # print(type(self._responder)) 封印　クラスを見るときに必要だったよ。
        parts = analyze(text)  # 追加
        if   isinstance(self._responder,TemplateResponder):
            response = self._responder.response(parts)
        elif isinstance(self._responder,MarkovResponder):
            response = self._responder.response(parts)
        else:
            response = self._responder.response(text)

        # response = self._responder.response(text, parts) #これじゃ見れなかったよ？

        self._dictionary.study(text, parts)  # 変更
        return response

    def save(self):
        """Dictionaryへの保存を行う。"""
        self._dictionary.save()

    @property
    def name(self):
        """人工無脳インスタンスの名前"""
        return self._name

    @property
    def responder_name(self):
        """保持しているResponderの名前"""
        return self._responder.name