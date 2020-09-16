
import Globals

import symengine as seng
import ops_def as ops
import utils
import logging
from gtokens import *

log = logging.getLogger(__name__)

class AST(object):
	"""The AST node: base class of all nodes.
	Arguments
	---------
	depth : int
		The depth of the node from the root. The default is 0.
	f_expression : string
		The expression represented by the node. Default is none.
	children : tuple of node type
		The children of the node. Can have at most 2 children. The default is an empty tuple.
	parents : set of node type
		The parent set of the node. Root node has no parent. The default is an empty set.
	noise : ?. The default is (0,0).
	rnd : float
		The rounding value at the node. The default is 1.0 implying no rounding necessary.
	"""
	__slots__ = ['depth', 'f_expression', 'children',\
	'parents', 'noise', 'rnd']

	def __init__(self):
		self.depth = 0
		self.f_expression = None
		self.children = ()
		self.parents = () #set()
		self.noise = (0,0)
		self.rnd = 1.0

	def __repr__(self):
		"""Representation of the AST node type
		Returns
		-------
		repr_str : str
			String representation of the class.
		"""
		parent_str = "("
		for i in range(len(self.parents)):
			parent_str=parent_str+self.parents[i].token.value+","
		parent_str=parent_str+")"
		repr_str = '\n\tdepth:' + repr(self.depth) \
				+ '\n\tparents:' + parent_str \
				+ '\n\tnoise:' + repr(self.noise) \
				+ '\n\trnd:' + repr(self.rnd)
		return repr_str

	#@staticmethod
	def set_expression(self, fexpr):
		""" Sets the f_expression class attribute.
		Parameters
		----------
		fexpr : string
			The expression represented by the node.
		"""
		self.f_expression = fexpr

	#@staticmethod
	def eval(obj):
		"""Directly returns the expression represented by the node without expanding further.
		Parameters
		----------
		obj : node type

		Returns
		-------
		obj.f_expression : string
			The expression represented by the node.
		"""
		return obj.f_expression

	@staticmethod
	def rec_eval(obj):
		"""Returns the expression represented by the node after expanding further.
		Parameters
		----------
		obj : node type

		Returns
		-------
		obj.eval(obj) : string
		"""
		return obj.eval(obj)

	@staticmethod
	def simplify(lexpr):
		"""Performs a check on the number of operations in the expression using the symengine library and expands if
		number of operations are within threshold specified.
		Parameters
		----------
		lexpr : symbolic expression

		Returns
		-------
		lexpr : symbolic expression
		"""
		#if not Globals.simplify or (seng.count_ops(lexpr) > 30000):
		#	return lexpr
		#else:
		#	lexpr2 = seng.expand(lexpr)
		#	op1 = seng.count_ops(lexpr)
		#	op2 = seng.count_ops(lexpr2)
		#	if (op2 - op1 > 1000):
		#		Globals.simplify = False
		#	return lexpr2 if(seng.count_ops(lexpr2) < seng.count_ops(lexpr)) else lexpr 

		##else:
		##	lexpr2 = seng.expand(lexpr)


		if(seng.count_ops(lexpr) > 30000):
			return lexpr
		else:
			return seng.expand(lexpr)
		return lexpr

	@staticmethod
	def get_noise(obj):
		return (seng.expand(obj.f_expression)) if obj.f_expression is not None else 0

	def set_rounding(self, rnd_type):
		self.rnd = ops._FP_RND[rnd_type]

	def get_rounding(self):
		return self.rnd * 1.0

class Num(AST):
	"""The Num node: Derived from AST representing numerical value holding nodes.
	Parameters
	----------
	token : Lexer Token object
	"""
	__slots__ = ['token']
	def __init__(self, token):
		super().__init__()
		self.token = token
		self.f_expression = self.eval(self)
		self.rnd = 0.0

	def __repr__(self):
		"""Representation of the Num node type
		Returns
		-------
		repr_str : str
			String representation of the class.
		"""
		repr_str = '\nNum{' + '\n\ttoken:' + repr(self.token) + super().__repr__() + '\n}'
		return repr_str
	
	@staticmethod
	def eval(obj):
		"""Returns the numerical value stored by the token.
		Parameters
		----------
		obj : node type

		Returns
		-------
		obj.token.value : int
			The value as parsed by the parser.
		"""
		return obj.token.value

	@staticmethod
	def get_noise(obj):
		return 0

class FreeVar(AST):
	"""The FreeVar node: Derived from AST representing abstracted nodes.
	Parameters
	----------
	token : Lexer Token object
	"""
	__slots__ = ['token']
	def __init__(self, token):
		super().__init__()
		self.token = token

	def __repr__(self):
		"""Representation of the FreeVar node type
		Returns
		-------
		repr_str : str
			String representation of the class.
		"""
		repr_str = '\nFreeVar{' + '\n\ttoken:' + repr(self.token) + super().__repr__() + '\n}'
		return repr_str
		
	@staticmethod
	def eval(obj, round_mode="fl64"):
		"""Sets rounding and returns the interval node or a new symengine variable.
		Parameters
		----------
		obj : node type
		round_mode : string
			Describes rounding mode at the node.

		Returns
		-------
		intv["INTV"][0] : interval node
		seng.var(name) : symengine variable
			Symengine variable called 'name'
		"""
		name = str(obj.token.value)
		obj.depth = 0
		obj.set_rounding(round_mode)
		intv = Globals.inputVars.get(obj.token.value, None)
		if intv is not None and (intv["INTV"][0]==intv["INTV"][1]):
			return intv["INTV"][0]
		else:
			return seng.var(name)

	@staticmethod
	def set_noise(obj, valueTup):
		obj.noise = valueTup


	@staticmethod
	def get_noise(obj, sound=False):
		return obj.noise if sound else \
		       abs(obj.noise[0]) if obj.noise is not None\
			   else 0

	def mutate_to_abstract(self, tvalue, tid):
		"""Sets the type and value of this nodes as its a FreeVariable and so is not parsed from any file.
		Parameters
		----------
		tvalue : Symengine variable
		tid : string
		"""
		self.token.value = tvalue
		self.token.type = tid

class Var(AST):
	"""The Var node: Derived from AST representing Input, Output and Expression variables.
	Parameters
	----------
	token : Lexer Token object
	"""
	__slots__ = ['token']
	def __init__(self, token):
		super().__init__()
		self.token = token

	def __repr__(self):
		"""Representation of the Var node type
		Returns
		-------
		repr_str : str
			String representation of the class.
		"""
		repr_str = '\nVar{' + '\n\ttoken:' + repr(self.token) + super().__repr__() + '\n}'
		return repr_str
		
	@staticmethod
	def eval(obj, round_mode="fl64"):
		"""Sets rounding and returns the expression at the node.
		Parameters
		----------
		obj : node type
		round_mode : string
			Describes rounding mode at the node.

		Returns
		-------
		obj.token.value/ node_lhs.f_expression : string
		"""
		#name = str(obj.token.value)
		obj.set_rounding(round_mode)
		node_lhs = Globals.symTable.get(obj.token.value, None)
		if node_lhs is None:
			return obj.token.value
		else:
			return node_lhs.f_expression
			#return node_lhs.eval()

class TransOp(AST):
	"""The TransOp node: Derived from AST representing unary operations.
	Parameters
	----------
	right : node type
		The only child/operand of this node
	token : Lexer Token object

	Notes
	-----
	These nodes have a single child and always called the right child.
	"""
	__slots__ = ['token']
	def __init__(self, right, token):
		super().__init__()
		self.token = token
		self.depth = right.depth+1
		self.children = (right,)
		right.parents += (self,)
		#right.parents.append(self)

	def __repr__(self):
		"""Representation of the TransOp node type
		Returns
		-------
		repr_str : str
			String representation of the class.
		"""
		repr_str = '\nTransOp{' + '\n\ttoken:' + repr(self.token) + super().__repr__() \
				+ '\n\tchildren:' + repr(self.children.token.value) \
				+ '\n}'
		return repr_str

	@staticmethod
	def eval(obj):
		"""Sets rounding and returns simplified symbolic expression without recursively building expression from child.
		Parameters
		----------
		obj : node type

		Returns
		-------
		lexpr : symbolic expression
		"""
		lexpr = ops._FOPS[obj.token.type]([obj.children[0].f_expression])
		obj.depth = obj.children[0].depth+1
		obj.rnd = obj.children[0].rnd
		lexpr =  obj.simplify(lexpr)
		#print(seng.count_ops(lexpr), obj.depth)
		return lexpr
		#return seng.expand(lexpr)

	@staticmethod
	def rec_eval(obj):
		"""Sets rounding, recursively builds expression from child and returns simplified expression.
		Parameters
		----------
		obj : node type

		Returns
		-------
		lexpr : symbolic expression
		"""
		lexpr = ops._FOPS[obj.token.type]([obj.children[0].rec_eval(obj.children[0])])
		obj.depth = obj.children[0].depth+1
		obj.rnd = obj.children[0].rnd
		return obj.simplify(lexpr)

	def get_rounding(self):
		return self.rnd * ops._ALLOC_ULP[self.token.type]

class BinOp(AST):
	"""The BinOp node: Derived from AST representing binary operations.
	Parameters
	----------
	left : node type
		The left child/operand of this node
	token : Lexer Token object
	right : node type
		The right child/operand of this node

	Notes
	-----
	These nodes have exactly two children.
	"""
	__slots__ = ['token']
	def __init__(self, left, token, right):
		super().__init__()
		self.token = token
		self.children = (left, right,)
		self.depth = max(left.depth, right.depth)+1
		left.parents += (self,)
		right.parents += (self,)
		#left.parents.add(self)
		#right.parents.add(self)

	def __repr__(self):
		"""Representation of the BinOp node type
		Returns
		-------
		repr_str : str
			String representation of the class.
		"""
		repr_str = '\nBinOp{' + '\n\ttoken:' + repr(self.token) + super().__repr__() \
				+ '\n\tleft child:' + repr(self.children[0].token.value) \
				+ '\n\tright child:' + repr(self.children[1].token.value) \
				+ '\n}'
		return repr_str

	@staticmethod
	def eval(obj):
		"""Sets rounding and returns simplified expression without recursively building expression.
		Parameters
		----------
		obj : node type

		Returns
		-------
		obj.simplify(lexpr)/lexpr : symbolic expression
		"""
		lexpr = ops._FOPS[obj.token.type]([child.f_expression for child in obj.children])
		obj.rnd = max([min([child.rnd for child in obj.children]), obj.rnd])
		if ((seng.Abs(obj.children[0].f_expression)==1.0 or \
		seng.Abs(obj.children[1].f_expression)==1.0) and obj.token.type==MUL):
			obj.rnd = 0.0
		#else:
		#	obj.rnd = max([min([child.rnd for child in obj.children]), 1.0])


		lexpr =  obj.simplify(lexpr)
		#print(seng.count_ops(lexpr), obj.depth)
		return lexpr
		#return obj.simplify(lexpr)

	@staticmethod
	def rec_eval(obj):
		"""Sets rounding, recursively builds expression from children and returns simplified expression..
		Parameters
		----------
		obj : node type

		Returns
		-------
		obj.simplify(lexpr) : symbolic expression
		"""
		ch_lexpr = [child.rec_eval(child) for child in obj.children]
		lexpr = ops._FOPS[obj.token.type](ch_lexpr)
		if (seng.Abs(ch_lexpr[0])==1.0 or \
		seng.Abs(ch_lexpr[1])==1.0):
			obj.rnd = 0.0
		else:
			obj.rnd = max([min([child.rnd for child in obj.children]), 1.0])


		return obj.simplify(lexpr)


	def get_rounding(self):
		return self.rnd * ops._ALLOC_ULP[self.token.type]

