import nltk
nltk.data.path.append('./nltk_data/')
from parse_forest_lib import *
from fsm_lib import *
import requests
from nltk import word_tokenize
from nltk.tree import MultiParentedTree
from awesome_print import ap
import copy
import re
from bllipparser import RerankingParser
import itertools
import urllib
import pydot
import os
from bllipparser.ModelFetcher import download_and_install_model
import re

if not os.path.exists(  os.path.join( os.getcwd(), "bllip", "models", "WSJ")  ):
	print "Downloading the BLLIP model ... "
	download_and_install_model('WSJ', os.path.join( os.getcwd(), "bllip", "models") )
	print "Done Downloading."

rrp = RerankingParser.from_unified_model_dir('bllip/models/WSJ')


def get_svg(data):
	graphs = pydot.graph_from_dot_data( data )
	svg_string = graphs[0].create_svg()
	return svg_string

def get_fsm_code(list_of_sentences):
	global rrp
	list_of_sentences = map( lambda sentence: (str(sentence)).lower(), list_of_sentences)
	list_of_sentences = map( lambda sentence:  re.sub(r'\..*', "", sentence ), list_of_sentences)
	list_of_parsed_strings = map( lambda sentence: rrp.simple_parse(sentence) , list_of_sentences)
	list_of_codified_parse_strings = map( lambda parse_string: ParseForest.codify_parse_string(parse_string) , list_of_parsed_strings)
	list_of_parse_forests = map( lambda codified_parse_string: ParseForest(codified_parse_string),  list_of_codified_parse_strings)
	# list_of_parse_forests = map( lambda codified_parse_string: ParseForest(codified_parse_string),  list_of_parsed_strings)

	merged_forest = ParseForest.merge_list_of_forests( list_of_parse_forests )
	aligned_paraphrases_lists = merged_forest.get_aligned_paraphrases()
	fsm = Fsm()
	for codified_parse_string in list_of_codified_parse_strings:
		fsm.load_tokens( ParseForest.get_codified_tokens(codified_parse_string) )

	for aligned_paraphrase_list in aligned_paraphrases_lists:
		for para_1, para_2 in itertools.combinations(aligned_paraphrase_list, 2):
			tokens_1 = word_tokenize( para_1 )
			tokens_2 = word_tokenize( para_2 )
			fsm.merge_parallel_tokens(tokens_1, tokens_2)

	fsm.sqeeze()
	# fsm.convert_to_word_edges()


	pre = "graph finite_state_machine {\n	rankdir=LR; \n        size=\"9,9\";\n"
	# start_end_definitions = "	node [shape = doublecircle ]; 1 2;\n".format(fsm.start.id, fsm.end.id)
	# node_definition = "	node [shape = circle ];\n"
	start_end_definitions = "	node [shape = doublecircle, width=.2, fixedsize=true, label=\"\"]; 1 2;\n".format(fsm.start.id, fsm.end.id)
	node_definition = "	node [shape = circle, width=.2, fixedsize=true, label=\"\" ];\n"
	fsm_commands = (fsm.get_graphvis_commands())
	fsm_commands = list( set(fsm_commands) )

	fsm_commands = map( lambda command: re.sub( r'(label = ")(\d+)', lambda match: match.group(1) + ParseForest.id_to_word_dictionary[int(match.group(2))] , command ) , fsm_commands)
	fsm_commands = list( set(fsm_commands) )

	transition_definitions = "\n".join( fsm_commands )
	post = "\n}"
	fsm_gv_code_snipped = pre + start_end_definitions + node_definition + transition_definitions + post

	return fsm_gv_code_snipped

# set(['17-26', '7-28', '9-4', '28-7', '3-8', '4-9', '13-20', '18-11', '11-18', '6-27', '12-19', '26-17', '20-13', '27-6', '14-21', '19-12', '21-14', '8-3'])
