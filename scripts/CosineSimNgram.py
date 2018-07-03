#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""

__author__ = "Aman Jain"

import argparse
import math
import os
import json
from numpy import dot
from CommentPreprocessor import preprocess
from CommentExtractor import CommentExtract
from getLicenses import fetch_licenses
from nltk.tokenize import word_tokenize
import textdistance

args = None


def l2_norm(a):
  a = [value for key, value in a.items()]
  return math.sqrt(dot(a, a))


def cosine_similarity(a, b):
  dot_product = 0
  for key, count in a.items():
    if key in b:
      dot_product += b[key] * count
  temp = l2_norm(a) * l2_norm(b)
  if temp == 0:
    return 0
  else:
    return dot_product / temp


def wordFrequency(arr):
  # arr = word_tokenize(a)
  frequency = {}
  for word in arr:
    if word in frequency:
      frequency[word] += 1
    else:
      frequency[word] = 1
  return frequency


def Ngram_guess(processedData):
  dir = os.path.dirname(os.path.abspath(__file__))
  with open(dir + '/database_keywordsNoStemSPDX.json', 'r') as file:
    unique_keywords = json.loads(file.read())

  initial_guess = []

  for keywords in unique_keywords:
    # print(keywords)
    matched_keys = 0
    for key in keywords['ngrams']:
      if key in processedData:
        matched_keys += 1
    if matched_keys > 0:
      initial_guess.append({
        'shortname': keywords['shortname'],
        'match': matched_keys / len(keywords['ngrams'])
      })
  if args is not None and args.verbose:
    print("Length of guess using ngram identifers ", len(initial_guess))
    initial_guess.sort(key=lambda x: x['match'], reverse=True)
    print(initial_guess)
  return initial_guess


def bigram_tokenize(s):
  return [s[i:i+2] for i in range(len(s) - 1)]


def NgramSim(inputFile, licenseList):
  commentFile = CommentExtract(inputFile)
  with open(commentFile) as file:
    data = file.read().replace('\n', ' ')
  processedData = preprocess(data)

  licenses = fetch_licenses(licenseList)
  Cosine_matches = []
  Dice_matches = []
  Bigram_cosine_matches = []

  initial_guess = Ngram_guess(processedData)
  for license in [x for x in licenses if x[0] in [y['shortname'] for y in initial_guess]]:
    # cosine similarity with unigram
    cosineSim = cosine_similarity(wordFrequency(word_tokenize(license[1])), wordFrequency(word_tokenize(processedData)))
    if cosineSim >= 0:
      Cosine_matches.append({
        'shortname': license[0],
        'cosineSim': cosineSim
      })
    if args is not None and args.verbose:
      print("Cosine Sim ", str(cosineSim), license[0])

    # dice similarity
    diceSim = textdistance.sorensen(word_tokenize(license[1]), word_tokenize(processedData))
    if diceSim >= 0:
      Dice_matches.append({
        'shortname': license[0],
        'diceSim': diceSim
      })
    if args is not None and args.verbose:
      print("Dice Sim ", str(diceSim), license[0])

    bigram_cosine_sim = cosine_similarity(wordFrequency(bigram_tokenize(license[1])), wordFrequency(bigram_tokenize(processedData)))
    if bigram_cosine_sim >= 0:
      Bigram_cosine_matches.append({
        'shortname': license[0],
        'bigram_cosine_sim': bigram_cosine_sim
      })
    if args is not None and args.verbose:
      print("Bigram Cosine Sim ", str(bigram_cosine_sim), license[0])

  result = []
  if len(Cosine_matches) > 0:
    if args is not None and args.verbose:
      print("Length of matches ", len(Cosine_matches))
    Cosine_matches.sort(key=lambda x: x['cosineSim'], reverse=True)
    result.append([])

  if len(Dice_matches) > 0:
    if args is not None and args.verbose:
      print("Length of matches ", len(Dice_matches))
    Dice_matches.sort(key=lambda x: x['diceSim'], reverse=True)
    result.append(Dice_matches)

  if len(Bigram_cosine_matches) > 0:
    if args is not None and args.verbose:
      print("Length of matches ", len(Bigram_cosine_matches))
    Bigram_cosine_matches.sort(key=lambda x: x['bigram_cosine_sim'], reverse=True)
    result.append(Bigram_cosine_matches)

  return result


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("inputFile", help="Specify the input file which needs to be scanned")
  parser.add_argument("licenseList", help="Specify the license list file which contains licenses")
  parser.add_argument("-v", "--verbose", help="increase output verbosity",
                      action="store_true")
  args = parser.parse_args()

  inputFile = args.inputFile
  licenseList = args.licenseList

  result = NgramSim(inputFile, licenseList)
  if len(result) > 0:
    print("N-Gram identifier and Vector space search ", str(result[0]) if len(result[0]) > 0 else "None")
    print("N-Gram identifier and Dice Similarity ", str(result[1]) if len(result[1]) > 0 else "None")
    print("N-Gram identifier and Bigram Cosine Similarity ", str(result[2]) if len(result[2]) > 0 else "None")
  else:
    print("Result is nothing")