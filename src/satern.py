

import sys
import time
import argparse 
import symengine as seng
#import subprocess
#
import Globals
from gtokens import *
from lexer import Slex
from parser import Sparser

from collections import defaultdict
from AnalyzeNode_Serial import AnalyzeNode_Serial
from ASTtypes import *
import helper 

import logging
DEBUG_LEVEL_ERR_ANALYSIS=9
DEBUG_LEVEL_PARSER=8


def parseArguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('--file', help='Test file name', required=True)
	parser.add_argument('--parallel', help='Enable parallel optimizer queries:use for large ASTs',\
							default=False, action='store_true')
	parser.add_argument('--enable-abstraction', help='Enable abstraction of internal node defintions,\
													  value indiactes level\
													  of abstraction. By default enabled to level-1. \
													  To disable pass 0', default=False, action='store_true')
	parser.add_argument('--mindepth', help='Min depth for abstraction. Default is 10',\
									  default=20, type=int)
	parser.add_argument('--maxdepth', help='Max depth for abstraction. Limiting to 40', \
									  default=40, type=int)
	#parser.add_argument('--fixdepth', help='Fix the abstraction depth. Default is -1(disabled)', \
	#								  default=-1, type=int)
	#parser.add_argument('--alg', help='Heuristic level for abstraction(default 0), \
	#									0 -> Optimal depth within mindepth and maxdepth(may loose correlation), \
	#									1 -> User defined fixed depth, \
	#									2 -> User Tagged nodes or only lhs nodes', \
	#									default=0, type=int)
	parser.add_argument('--simplify', help='Simplify expression -> could be costly for very large expressions',
										default=False, action='store_true')
	parser.add_argument('--logfile', help='Python logging file name -> default is default.log', default='default.log')
	parser.add_argument('--loglevel', help='Python logging level -> default level is "INFO" which has value 20',
						default=20, type=int)
	parser.add_argument('--outfile', help='Name of the output file to write error info', default='outfile.txt')
	parser.add_argument('--std', help='Print the result to stdout', default=False, action='store_true')
	parser.add_argument('--sound', help='Turn on analysis for higher order errors', default=False, action='store_true')
	parser.add_argument('--compress', help='Perform signature matching to reduce optimizer calls using hashing and md5 signature', default=False, action='store_true')
	parser.add_argument('--force', help='Sideline additional tricks used for non-linear examples. Use this option for linear examples', default=False, action='store_true')
	                                  

	result = parser.parse_args()
	return result


def rebuildASTNode(node, completed):
	
	for child in node.children:
		if not completed.__contains__(child):
			rebuildASTNode(child, completed)

	node.depth = 0 if len(node.children)==0 else max([child.depth for child in node.children])+1
	completed[node] = node.depth

def rebuildAST():
	print("\n********* Rebuilding AST post abstracttion ********\n")
	print("Synthesizing expression with fresh FreeVars .... ")
	logger.info("\n********* Rebuilding AST post abstracttion ********\n")
	logger.info("Synthesizing expression with fresh FreeVars .... ")
	probeList = helper.getProbeList()

	completed = defaultdict(int) ## node -> depth

	for node in probeList:
		if not completed.__contains__(node):
			rebuildASTNode(node, completed)

	rev_symTable = {v : k for k,v in Globals.symTable.items()}
	Globals.symTable = {syms : node for node,syms in rev_symTable.items() \
	                      if completed.__contains__(node)}


	maxdepth = max([node.depth for node in probeList])
	Globals.depthTable = { depth : set([ node for node in completed.keys() if node.depth==depth]) for depth in range(maxdepth+1)}
	del probeList
	del completed
	del rev_symTable


	
			

def abstractNodes(results):

	rev_symTable = {v : k for k,v in Globals.symTable.items()}

	for node, res in results.items():
		Globals.FID += 1
		name = seng.var("_F"+str(Globals.FID))
		name = rev_symTable.get(node, name)
		node.__class__ = FreeVar
		node.children = ()
		node.depth = 0

		node.set_noise(node, (res["ERR"], res["SERR"]))
		node.mutate_to_abstract(name, ID)

		#errWidth = (res["ERR"]+res["SERR"])*pow(2, -53)
		#intv = [res["INTV"][0] - errWidth, res["INTV"][1] + errWidth]

		#Globals.inputVars[name] = {"INTV" : intv}
		Globals.inputVars[name] = {"INTV" : res["INTV"]}
		Globals.symTable[name] = node

	del rev_symTable




def simplify_with_abstraction(sel_candidate_list, argList, maxdepth, force=False, final=False):
	if(final==True):
		log.debug_err_analysis("Direct Solving")
	# if argList.loglevel<=9:
	# 	sel_candidate_str="["
	# 	for i in range(len(sel_candidate_list)):
	# 		sel_candidate_str = sel_candidate_str + sel_candidate_list[i].token.value + ","
	# 	sel_candidate_str = sel_candidate_str + "]"

		# log.debug_err_analysis("Candidate list:" + sel_candidate_str)

	obj = AnalyzeNode_Serial(sel_candidate_list, argList, maxdepth, force)
	results = obj.start()
	log.debug_err_analysis("Result of Analysis:" + str(results))
	if "flag" in results.keys():
		print("Returned w/o execution-->need to modify bound")
		return results

	del obj
	if final:
		#for k,v in results.items():
		#	print(k.f_expression)
		return results

	abstractNodes(results)
	rebuildAST()
	return dict()



def full_analysis(probeList, argList, maxdepth):
	#probeList = [it[1] for it in list(filter(lambda x: x[0] in globals.outVars, \
	#                        [[k,v] for k,v in globals.lhstbl.items()]))]

	return simplify_with_abstraction(probeList, argList, maxdepth, force=True, final=True)


def	ErrorAnalysis(argList):

	absCount = 1
	probeList = helper.getProbeList()
	maxdepth = max([node.depth for node in probeList])

	logger.info("AST_DEPTH : {AST_DEPTH}".format(AST_DEPTH = maxdepth))

	bound_mindepth , bound_maxdepth = argList.mindepth, argList.maxdepth

	if ( argList.enable_abstraction ) :
		print("Abstraction Enabled... \n")
		while ( maxdepth >= bound_maxdepth and maxdepth >= bound_mindepth):
			[abs_depth,sel_candidate_list] = helper.selectCandidateNodes(maxdepth, bound_mindepth, bound_maxdepth)
			print("Canidate List Length:", len(sel_candidate_list))
			log.debug_err_analysis("Abs depth:" + str(abs_depth))
			if ( len(sel_candidate_list) > 0 ):
				absCount += 1
				results = simplify_with_abstraction(sel_candidate_list, argList, maxdepth)
				maxopCount = results.get("maxOpCount", 1000)
				probeList = helper.getProbeList()
				maxdepth = max([node.depth for node in probeList]) -1
				if (maxopCount > 1000 and maxdepth > 8 and bound_mindepth > 5):
					bound_maxdepth = maxdepth if bound_maxdepth > maxdepth else bound_maxdepth - 2 if bound_maxdepth - bound_mindepth > 4 else bound_maxdepth
					bound_mindepth = bound_mindepth - 2 if bound_maxdepth - bound_mindepth > 4 else bound_mindepth
				elif maxdepth <= bound_maxdepth and maxdepth > bound_mindepth:
					bound_maxdepth = maxdepth
					assert(bound_maxdepth >= bound_mindepth)
			else:
				break
		print("Bypassing abstraction\n")
		print(maxdepth, bound_maxdepth, bound_mindepth)
		#print("Expr->", probeList[0].f_expression)
		logger.info("BYPASSING_ABSTRACTION\n\n")
		return full_analysis(probeList, argList, maxdepth)
	else:
		return full_analysis(probeList, argList, maxdepth)
	

def debug_err_analysis(self, message, *args, **kws):
    if self.isEnabledFor(DEBUG_LEVEL_ERR_ANALYSIS):
        # Yes, logger takes its '*args' as 'args'.
        self._log(DEBUG_LEVEL_ERR_ANALYSIS, message, args, **kws)

def debug_parser(self, message, *args, **kws):
    if self.isEnabledFor(DEBUG_LEVEL_PARSER):
        # Yes, logger takes its '*args' as 'args'.
        self._log(DEBUG_LEVEL_PARSER, message, args, **kws)

if __name__ == "__main__":
	start_exec_time = time.time()
	argList = parseArguments()
	sys.setrecursionlimit(10**6)
	print(argList)
	text = open(argList.file, 'r').read()
	fout = open(argList.outfile, 'w')
	##-----------------------
	logging.addLevelName(DEBUG_LEVEL_ERR_ANALYSIS, "DEBUG_ERR_ANALYSIS")
	logging.addLevelName(DEBUG_LEVEL_PARSER, "DEBUG_PARSER")

	logging.basicConfig(filename= argList.logfile,
					level = argList.loglevel,
					filemode = 'w')
	logging.Logger.debug_err_analysis = debug_err_analysis
	logging.Logger.debug_parser = debug_parser
	logger = logging.getLogger()
	##-----------------------
	logger.debug_err_analysis("Hello Im the new logger")
	start_parse_time = time.time()
	lexer = Slex()
	parser = Sparser(lexer)
	parser.parse(text)
	del parser
	del lexer
	end_parse_time = time.time()
	parse_time = end_parse_time - start_parse_time
	logger.info("Parsing time : {parse_time} secs".format(parse_time = parse_time))

	##----- PreProcess to eliminate all redundant defintions ------
	pr1=time.time()
	helper.PreProcessAST()
	pr2=time.time()
	
	ea1 = time.time()
	results = ErrorAnalysis(argList)
	ea2 = time.time()
	helper.writeToFile(results, fout, argList.file, argList.std, argList.sound)
	#writeToFile(results)





	end_exec_time = time.time()
	##------ End of Analysis Results ------
	fout.write("Optimizer Calls: {num_calls}\n".format(num_calls = Globals.gelpiaID))
	fout.write("Parsing time : {parsing_time}\n".format(parsing_time = parse_time))
	fout.write("PreProcessing time : {preprocess_time}\n".format(preprocess_time = pr2-pr1))
	fout.write("Analysis time : {analysis_time}\n".format(analysis_time = ea2-ea1))
	fout.write("Full time : {full_time}\n".format(full_time = end_exec_time-start_exec_time))
	logger.info("Optimizer Calls: {num_calls}".format(num_calls = Globals.gelpiaID))
	logger.info("Parsing time : {parsing_time}".format(parsing_time = parse_time))
	logger.info("PreProcessing time : {preprocess_time}".format(preprocess_time = pr2-pr1))
	logger.info("Analysis time : {analysis_time}".format(analysis_time = ea2-ea1))
	logger.info("Full time : {full_time}".format(full_time = end_exec_time-start_exec_time))
	print("Optimizer Calls: {num_calls}".format(num_calls = Globals.gelpiaID))
	print("Parsing time : {parsing_time}\n".format(parsing_time = parse_time))
	print("PreProcessing time : {preprocess_time}\n".format(preprocess_time = pr2-pr1))
	print("Analysis time : {analysis_time}\n".format(analysis_time = ea2-ea1))
	print("Full time : {full_time}\n".format(full_time = end_exec_time-start_exec_time))
	fout.close()



