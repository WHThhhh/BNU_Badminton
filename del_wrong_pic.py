import os
import glob

ans_txt = glob.glob('./Valid_pic/*.txt')
ans_pic = glob.glob('./Valid_pic/*.png')

wrong_pic = [p for p in ans_pic if p.replace('png', 'txt') not in ans_txt]
for w in wrong_pic:
    os.remove(w)
