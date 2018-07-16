import sys
import argparse
import json, pickle
import StringIO,operator

class Model(object):

    def __init__(self, model_path):
        self.reverse_mapping = dict()
        self.word_mapping = dict()
        self.word_mapping = pickle.load(open(model_path, 'rb'))
        print("load model")
        self.word_cnt = len(self.word_mapping) +1
        for k, v in self.word_mapping.items():
            self.reverse_mapping[v] = k


class Solver(object):
    """docstring for PreProcessor"""
    def __init__(self, Model):
        #self.punc_mapping = dict()
        self.word_mapping = Model.word_mapping
        self.reverse_mapping = Model.reverse_mapping
        self.word_cnt = Model.word_cnt
        self.punc = {'.',',','"',"'",'?',':',';','-','!','-lrb-','-rrb-','``',"''", ''}
        self.fdep = ''
        self.fpos = ''
        self.fdoc = ''
        self.fems = ''
        self.test_tokens = []
        self.test_words = []
    def case(self, w):
        if w.isupper() or w in self.punc:
            return '3'
        elif w[0].isupper():
            return '1'
        elif w.isdigit():
            return '4'
        else:
            return '0'

    def inWordmapping(self,word):
        if word not in self.word_mapping:
            self.word_mapping[word]=self.word_cnt
            # if word in self.punc:
            #     self.punc_mapping[self.word_cnt] = word
            #self.reverse_mapping[self.word_cnt]=word
            self.word_cnt+=1

        return str(self.word_mapping[word])

    def extract_transformat(self,inp,json_file,pos_file):
        e_not_found = 0
        cnt = 0
        remine_seg = inp.split('\n')
        test_lemma = json_file.split('\n')
        test_pos = pos_file.split('\n')
        output = []
        #print('total_remine', remine_seg)

        for line, json_line, pos_line in zip(remine_seg, test_lemma, test_pos):
            #print("remine_seg",line)
            cnt += 1
            pred=[]
            pred_rm = []
            for item in line.split(']_['):
                if ':EP' in item:
                    pred.append(item.rstrip(' :EP').strip().replace('(','-lrb-').replace(')','-rrb-'))
                elif ':BP' in item:
                    pred.append(item.rstrip(' :BP').strip().replace('(','-lrb-').replace(')','-rrb-'))
            tmp = {}
            tmp['tokens'] = json_line.strip().split(' ')
            #tmp['lemmas'] =
            tmp['pos'] = pos_line.strip().split(' ')
            #exists = set()
            cur_max = dict()
            tmp['entityMentions'] = []
            ptr = 0
            for e in pred:
                window_size=e.count(' ') + 1

                found=False
                #ptr = 0
                while ptr+window_size <= len(tmp['tokens']):
                    if ' '.join(tmp['tokens'][ptr:ptr+window_size]) == e:
                        found=True
                        break
                    ptr+=1
                #if found and (ptr, ptr+window_size) not in exists:
                if not found:
                    ptr = 0
                    #print(e+"not found")
                    e_not_found += 1
                if found:
                    if ptr+window_size not in cur_max:
                        cur_max[ptr+window_size] = ptr
                        #tmp['entityMentions'].append([ptr, ptr+window_size, e])
                    ptr+=window_size
            #keys = cur_max.keys().sort(reverse=True)
            ptr = len(tmp['tokens'])
            while ptr > 0:
                if ptr in cur_max:
                    tmp['entityMentions'].append([cur_max[ptr], ptr, ' '.join(tmp['tokens'][cur_max[ptr]:ptr])])
                    ptr = cur_max[ptr]
                else:
                    ptr -= 1

            #tmp['entityMentions'] = list(exists)
            tmp['entityMentions'].sort(key=operator.itemgetter(1))


            new = []
            for i in range(len(tmp['entityMentions'])-1):
                if tmp['entityMentions'][i][1] == tmp['entityMentions'][i+1][0] and (tmp['entityMentions'][i+1][2][0:2] == 'of' or tmp['entityMentions'][i][2][-2:] == 'of' or tmp['entityMentions'][i+1][2][0:2] == "'s" or tmp['entityMentions'][i][2][-2:] == "'s"):
                    postags = ''.join(tmp['pos'][tmp['entityMentions'][i][0]:tmp['entityMentions'][i+1][1]])
                    if 'NN' in postags or 'W' in postags:
                        new.append([tmp['entityMentions'][i][0], tmp['entityMentions'][i+1][1], tmp['entityMentions'][i][2] + ' ' + tmp['entityMentions'][i+1][2]])
                        #if cnt >= 235973:
                            #print(tmp['entityMentions'][i][2], tmp['entityMentions'][i+1][2])
                        #if tmp['']
                    #else:
                    #   print(tmp['entityMentions'][i][2] + ' ' + tmp['entityMentions'][i+1][2])
                    #print(new[-1][2])
                elif len(new) == 0 or tmp['entityMentions'][i][0] >= new[-1][1]:
                    postags = ''.join(tmp['pos'][tmp['entityMentions'][i][0]:tmp['entityMentions'][i][1]])
                    if 'NN' in postags or 'W' in postags or 'PRP' in postags:
                        new.append(tmp['entityMentions'][i])
                    #else:
                    #   print(tmp['entityMentions'][i][2])
            if len(new) == 0:
                new = tmp['entityMentions']
            elif new[-1][1] != tmp['entityMentions'][-1][1]:
                new.append(tmp['entityMentions'][-1])

            for idx,item in enumerate(new):
                postags = tmp['pos'][item[0]:item[1]]
                start = int(item[0])
                end = int(item[1])
                xxxx = item[2].strip().split(' ')
                if postags[0] == 'IN' or postags[0] == 'CC' or postags[0] == 'TO':
                    del xxxx[0]
                    start += 1
                if len(xxxx) > 0:
                    if postags[-1] == 'IN' or postags[-1] == 'CC' or postags[-1] == 'TO':
                        del xxxx[-1]
                        end -= 1
                if start != int(item[0]) or end != int(item[1]):
                    if start != end:
                        new[idx] = [start, end, ' '.join(xxxx)]
                        #print(item[2], ' '.join(xxxx))
                    else:
                        pass
                        #print("^^^^^^^"+item[2]+"^^^^^^^")
            tmp['entityMentions'] = new


            output.append(tmp)

        emsIO = StringIO.StringIO()
        for tmp in output:
                #print("tmp",tmp)
                ems = ''
                for em in tmp['entityMentions']:
                    if len(em[2]) > 0:
                        ems += str(em[0]) + '_'  + str(em[1]) + ' '
                emsIO.write(ems.strip()+'\n')
            #print("#entity not found:",e_not_found)
        self.fems = emsIO.getvalue()
    def tokenized_test(self, docIn, posIn, depIn):
        docin = docIn.split('\n')
        posin = posIn.split('\n')
        depin = depIn.split('\n')

        depIO = StringIO.StringIO()
        posIO = StringIO.StringIO()
        docIO = StringIO.StringIO()

        for t,p,d in zip(docin,posin,depin):
            _word = []
            _token = []
            tokens = t.strip().split(' ')
            postags = p.strip().split(' ')
            deps = d.strip().split(' ')
            tmp = []
            for i,d in enumerate(deps):
                #dd=d.split('_')
                tmp.append(str(i)+'_'+d)
            assert(len(tokens) == len(postags) == len(deps))
            #print(tokens)
            for i,w in enumerate(tokens):
                if i != len(tokens) - 1:
                    docIO.write(self.inWordmapping(w) + ' ')
                    _token.append(self.inWordmapping(w))
                else:
                    #if w not in self.punc:
                    docIO.write(self.inWordmapping(w) + '\n')
                    _token.append(self.inWordmapping(w))
                    #else:
                        #fdoc.write(w+'\n')
                        #_token.append(w)
                _word.append(w)
            self.test_tokens.append(_token)
            self.test_words.append(_word)

            depIO.write(('\n'.join(tmp)) + '\n')
            posIO.write(('\n'.join(postags)) + '\n')

        self.fdoc = docIO.getvalue()
        self.fdep = depIO.getvalue()
        self.fpos = posIO.getvalue()



    def load(self):
        self.word_mapping = pickle.load(open('tmp_remine/token_mapping.p', 'rb'))



    def tokenize(self, docIn, docOut):
        with open(docIn, encoding='utf-8') as doc, open(docOut,'w', encoding='utf-8') as out:
            for line in doc:
                tmp = line.strip().split(' ')
                out.write(' '.join(list(map(lambda x: self.inWordmapping(x), tmp)))+'\n')


    def mapBackv2(self,seg_path):
        queue=[]
        r_ptr=0
        c_ptr=0
        start=['<None>','<EP>','<RP>','<BP>']
        end=['</None>','</EP>','</RP>', '</BP>']
        start_phrase=False
        output = StringIO.StringIO()
        list_seg_path = seg_path.split('\n')

        for line in list_seg_path[:len(list_seg_path)-1]:
            for token in line.strip().split(' '):
                queue.append(token)
            #print queue
            while (len(queue)>0):
                #print c_ptr,r_ptr
                if queue[0] in start or queue[0] in end:
                    #if queue[0] == '</phrase>' or c_ptr < len(self.test_token[r_ptr]):
                    if queue[0] in start and c_ptr == len(self.test_tokens[r_ptr]):
                        #OUT.write('\n'+queue.pop(0)+' ')
                        start_phrase=True
                        output.write('\n')
                        r_ptr+=1
                        c_ptr=0
                        queue.pop(0)
                        continue
                    else:
                        if queue[0] in start:
                            start_phrase=True
                        else:
                            start_phrase=False
                            if 'None' in queue[0]:
                                #OUT.write(':BP,')
                                output.write(']_[')
                            elif 'EP' in queue[0]:
                                output.write(':EP]_[')
                            elif 'RP' in queue[0]:
                                output.write(':RP]_[')
                            elif 'BP' in queue[0]:
                                output.write(':BP]_[')
                        queue.pop(0)

                elif c_ptr < len(self.test_tokens[r_ptr]) and queue[0] == self.test_tokens[r_ptr][c_ptr]:
                    if start_phrase:
                        output.write(self.test_words[r_ptr][c_ptr] + ' ')
                    else:
                        output.write(self.test_words[r_ptr][c_ptr] + ']_[')
                    queue.pop(0)
                    c_ptr+=1
                else:
                    r_ptr+=1
                    c_ptr=0
                    output.write('\n')
        return output.getvalue()

    def map(self,seg_path,outpath):
        queue=[]
        r_ptr=0
        c_ptr=0
        start=['<None>','<EP>','<RP>','<BP>']
        end=['</None>','</EP>','</RP>', '</BP>']
        start_phrase=False
        with open(seg_path,'r', encoding='utf-8') as _seg, open(outpath,'w', encoding='utf-8') as OUT:
            for line in _seg:
                for token in line.strip().split(' '):
                    queue.append(token)
                #print queue
                while (len(queue)>0):
                    #print c_ptr,r_ptr
                    if queue[0] in start or queue[0] in end:
                        #if queue[0] == '</phrase>' or c_ptr < len(self.test_token[r_ptr]):
                        if queue[0] in start and c_ptr == len(self.test_tokens[r_ptr]):
                            #OUT.write('\n'+queue.pop(0)+' ')
                            start_phrase=True
                            OUT.write('\n')
                            r_ptr+=1
                            c_ptr=0
                            queue.pop(0)
                            continue
                        else:
                            if queue[0] in start:
                                start_phrase=True
                            else:
                                start_phrase=False
                                if 'None' in queue[0]:
                                    #OUT.write(':BP,')
                                    OUT.write(']_[')
                                elif 'EP' in queue[0]:
                                    OUT.write(':EP]_[')
                                elif 'RP' in queue[0]:
                                    OUT.write(':RP]_[')
                                elif 'BP' in queue[0]:
                                    OUT.write(':BP]_[')
                            queue.pop(0)
                    elif c_ptr < len(self.test_tokens[r_ptr]) and queue[0] == self.test_tokens[r_ptr][c_ptr]:
                        if start_phrase:
                            OUT.write(self.test_words[r_ptr][c_ptr] + ' ')
                        else:
                            OUT.write(self.test_words[r_ptr][c_ptr] + ']_[')
                        queue.pop(0)
                        c_ptr+=1
                    else:
                        r_ptr+=1
                        c_ptr=0
                        OUT.write('\n')




    def translate(self, line):
        lines = line.split("\n")

        for i in range(len(lines)-1):
            temp = lines[i].replace('\t', '|')

            temp = temp.split("|")
            temp[2] = temp[2].split(",")[:-1]
            temp[3] = temp[3][1:]
            lines[i] = temp
        for i in range(len(lines)-1):
            # ob
            lines[i][1] = " ".join([self.reverse_mapping[int(t)] for t in lines[i][1].split(" ")])
            # relation
            line_temp = []
            for word in lines[i][2]:
                temp = word[1:-1].split(" ")
                temp = [self.reverse_mapping[int(t)] for t in temp]
                str_temp = " "
                for t in temp:
                    str_temp = str_temp + t + " "
                line_temp.append(str_temp)
            lines[i][2] = ",".join(line_temp) + ", "
            # sb
            lines[i][3] = " " + " ".join([self.reverse_mapping[int(t)] for t in lines[i][3].split(" ")])
            lines[i] = list("|".join(lines[i]))
            for t in range(len(lines[i])):
                if lines[i][t] == "|":
                    lines[i][t] = "\t"
                    break
            lines[i] = "".join(lines[i])

        lines = "\n".join(lines)
        return lines








