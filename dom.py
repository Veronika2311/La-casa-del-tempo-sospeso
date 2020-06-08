import telebot  # импортируем модуль pyTelegramBotAPI
import conf     # импортируем наш секретный токен
import random
import requests
import sqlite3
import gensim
import markovify
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()

# telebot.apihelper.proxy = {'https': 'socks5h://geek:socks@t.geekclass.ru:7777'} #задаем прокси
telebot.apihelper.proxy = conf.PROXY
bot = telebot.TeleBot(conf.TOKEN)  # создаем экземпляр бота

model_dom = gensim.models.KeyedVectors.load_word2vec_format('dom_pos.bin', binary=True)
model_dom_lemm = gensim.models.KeyedVectors.load_word2vec_format('dom_pos_lemm.bin', binary=True)
with open("only_dom.json", encoding='utf-8') as f:
    m = f.read()
marcov_model = markovify.Text.from_json(m)

def givetext(randtxt):
    #Определяется, как будет создан сгенерированный текст
    #randtxt = random.randint(0, 4)
    #randtxt = 3
    #текст из "Дома"
    randids = random.randint(5, 28872)
    conn = sqlite3.connect('dom.db')
    cur = conn.cursor()
    cur.execute('SELECT sentence, lenwords FROM sentences WHERE ids = ?', (randids,))
    #сonn.close()
    a = cur.fetchall()
    lenwords = a[0][1]
    text = [a[0][0]]
    n = 1
    ids = [randids, ]
    while lenwords < 30:
        cur.execute('SELECT sentence, lenwords FROM sentences WHERE ids = ?', (randids + n,))
        a = cur.fetchall()
        text.append(a[0][0])
        ids.append(randids + n)
        lenwords += a[0][1]
        n += 1
    
    if randtxt == 0:
        new_text = ' '.join(text)
        new_text = new_text + ' \n\nЭто оригинальный текст'
        
    elif randtxt == 1:
        
        forms = []
        for one_ids in ids:
            cur.execute('SELECT word, POS FROM words WHERE ids = ?', (one_ids,))
            a = cur.fetchall()
            for one_word in a:
                if one_word[1] != None:
                    forms.append('_'.join(one_word))
                else:
                    forms.append(one_word[0])
        
        count = 0
        new_forms = []
        for form in forms:
            if form in model_dom:
                new_word = model_dom.wv.most_similar(form, topn=1)[0][0]
                new_forms.append(new_word.split('_')[0])
                count += 1
            else:
                new_forms.append(form.split('_')[0])           
        
        if count != 0:
            new_text = ''
            for word in new_forms:
                if word in '\".,!?:;':
                    new_text = new_text + word
                else:
                    new_text = new_text + ' ' + word
            new_text = new_text + ' \n\n Это замена всех слов с помощью модели, обученной на Доме. Исходный текст: \n\n' + ' '.join(text)

    elif randtxt == 2:
        
        forms = []
        for one_ids in ids:
            cur.execute('SELECT word, POS FROM words WHERE ids = ?', (one_ids,))
            a = cur.fetchall()
            for one_word in a:
                if one_word[1] != None:
                    forms.append('_'.join(one_word))
                else:
                    forms.append(one_word[0])
        
        count = 0
        new_forms = []
        in_model = []
        for form in forms:
            if form in model_dom and not form.endswith('PREP'):
                count += 1
                in_model.append(form)
        if count >= 5:
            sampl = random.choices(in_model, k=5)
        else: 
            sampl = forms
        for form in forms:
            if form in sampl:
                if form in model_dom:
                    new_word = model_dom.wv.most_similar(form, topn=1)[0][0]
                    new_forms.append(new_word.split('_')[0])
            else:
                new_forms.append(form.split('_')[0])           
        
        if count != 0:
            new_text = ''
            for word in new_forms:
                if word in '\".,!?:;':
                    new_text = new_text + word
                else:
                    new_text = new_text + ' ' + word
            new_text = new_text + ' \n\nЭто замена части слов с помощью модели, обученной на Доме. Исходный текст: \n\n' + ' '.join(text)
            
    elif randtxt == 3:
        
        words = []
        forms = []
    
        for one_ids in ids:
            cur.execute('SELECT word, normal_form, POS FROM words WHERE ids = ?', (one_ids,))
            a = cur.fetchall()
            for one_word in a:
                words.append(one_word[0])
                if one_word[2] != None:
                    forms.append('_'.join(one_word[1:]))
                else:
                    forms.append(one_word[1])
        
        count = 0

        for i, form in enumerate(forms):
            if form in model_dom:
                for ind in range(15):
                    new_word = model_dom_lemm.wv.most_similar(form, topn=15)[ind][0]
                    if form[-3:-1] == new_word[-3:-1]: #часть речи
                        break
                    
                parseword = morph.parse(new_word.split('_')[0])
                    
                for el in parseword:
                    grams = str(morph.parse(words[i])[0][1]).split(' ')[-1]
                    lexnewword = el.lexeme
                    for p in lexnewword:
                        if str(p[1]).split(' ')[-1] == grams:
                            word_to_text = str(p[0])
                            words[i] = word_to_text

        new_text = ''
        for word in words:
            if word in '\".,!?:;':
                new_text = new_text + word
            else:
                new_text = new_text + ' ' + word
        new_text = new_text + ' \n\nЭто замена части лемм с помощью модели, обученной на Доме. Исходный текст: \n\n' + ' '.join(text)    

            
    elif randtxt == 4:
        new_text = ''
        for i in range(7):
            new_text += marcov_model.make_short_sentence(1000) + ' '
        new_text = new_text + ' \n\nЭто марковская цепь, обученная только на Доме'
 
            
    #text = ' '.join(text)    
    return new_text

            
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     """Здравствуйте! Этот бот выдаёт отрывки текста из книги 'Дом, в котором...'
                     или сгенерированные на основе книги. Вы можете использовать команду '/text' для случайного отрывка или 
                     '/dom' для текста Мариам Петросян, '/marcovdom' для марковской цепи, '/w2v1', '/w2v2', '/w2v3' -- для 
                     вариантов изменения текста с заменами близких слов с помощью word2vec""")

@bot.message_handler(commands=['text'])
def send_text(message):
    randtxt = random.randint(0, 4)
    text = givetext(randtxt)
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['dom'])
def send_text(message):
    text = givetext(0)
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['marcovdom'])
def send_text(message):
    text = givetext(4)
    bot.send_message(message.chat.id, text) 
    
@bot.message_handler(commands=['w2v1'])
def send_text(message):
    text = givetext(1)
    bot.send_message(message.chat.id, text)
    
@bot.message_handler(commands=['w2v2'])
def send_text(message):
    text = givetext(2)
    bot.send_message(message.chat.id, text)
    
@bot.message_handler(commands=['w2v3'])
def send_text(message):
    text = givetext(3)
    bot.send_message(message.chat.id, text)

# этот обработчик реагирует на любое сообщение
@bot.message_handler(func=lambda m: True)
def bop(message):
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    bot.send_message(message.chat.id, 'К сожалению, я не понимаю Вас')
    bot.send_photo(chat_id=message.chat.id, photo=url)
    

if __name__ == '__main__':
    bot.polling(none_stop=True)