
# stencil basic spec
# A[(i,j), t] = 0.125 * A[(i-1,j),t-1] + 0.125 * A[(i+1,j), t-1] \
#				0.125 * A[(i,j-1),t-1] + 0.125 * A[(i,j+1), t-1] \
#				0.5   * A[(i,j), t-1]

import sys

def get_sign(index, mid):
	return 'p' if index > mid else 'm' if index < mid else ''

def gen_stencil2d_cse():

	west =  "0.125"
	east =   "0.125"
	north =  "0.125"
	south =  "0.125"
	center = "0.5"

	T = int(sys.argv[1])
	mid0, mid1 = T, T

	A = [[[None]*(2*T+1) for i in range(0,2*T+1)] for j in range(0,2)]

	fout = open("h2d_cse_t"+str(T)+".txt", 'w')

	for t in range(0, T+1):
		for i in range(mid0-(T-t), mid0+(T-t)+1):
			for j in range(mid1-(T-t), mid1+(T-t)+1):
				if t==0 :
					inp = "x{signx}{posx}_{signy}{posy}_{tstamp} : ({lb}, {ub});\n".format( \
								signx = get_sign(i, mid0),\
					            signy = get_sign(j, mid1),\
								posx  = str(abs(mid0-i)), \
								posy  = str(abs(mid1-j)), \
								tstamp = str(t), \
								lb = float(sys.argv[2]), \
								ub = float(sys.argv[3]) \
							  )
					fout.write(inp)					
				else:
					print(t,i,j)
					lhs = "x{signx}{posx}_{signy}{posy}_{tstamp}".format(\
								signx = get_sign(i, mid0),\
					            signy = get_sign(j, mid1),\
								posx  = str(abs(mid0-i)), \
								posy  = str(abs(mid1-j)), \
								tstamp = str(t) \
							  )
	
					west_rhs = "{coeff} * x{signx}{posx}_{signy}{posy}_{tstamp}".format(\
									  coeff = west, \
									  signx = get_sign(i-1, mid0), \
									  signy = get_sign(j, mid1), \
									  posx  = str(abs(mid0 - (i-1))), \
									  posy  = str(abs(mid1 - j)), \
									  tstamp = str(t-1) \
								    )
	
					east_rhs = "{coeff} * x{signx}{posx}_{signy}{posy}_{tstamp}".format(\
									  coeff = east, \
									  signx = get_sign(i+1, mid0), \
									  signy = get_sign(j, mid1), \
									  posx  = str(abs(mid0 - (i+1))), \
									  posy  = str(abs(mid1 - j)), \
									  tstamp = str(t-1) \
								    )
	
					north_rhs = "{coeff} * x{signx}{posx}_{signy}{posy}_{tstamp}".format(\
									  coeff = north, \
									  signx = get_sign(i, mid0), \
									  signy = get_sign(j+1, mid1), \
									  posx  = str(abs(mid0 - (i))), \
									  posy  = str(abs(mid1 - (j+1))), \
									  tstamp = str(t-1) \
								    )
	
					south_rhs = "{coeff} * x{signx}{posx}_{signy}{posy}_{tstamp}".format( \
									  coeff = south, \
									  signx = get_sign(i, mid0), \
									  signy = get_sign(j-1, mid1), \
									  posx  = str(abs(mid0 - (i))), \
									  posy  = str(abs(mid1 - (j-1))), \
									  tstamp = str(t-1), \
								    )
	
					center_rhs = """{coeff} * x{signx}{posx}_{signy}{posy}_{tstamp}""".format(  \
									  coeff = center, \
									  signx = get_sign(i, mid0), \
									  signy = get_sign(j, mid1), \
									  posx  = str(abs(mid0 - (i))), \
									  posy  = str(abs(mid1 - (j))), \
									  tstamp = str(t-1) \
								    )
	
					expr = "{lhs} = ({west} + {east} + {north} + {south} + {center});".format(\
								  lhs = lhs, \
								  west= west_rhs, \
								  east= east_rhs, \
								  north= north_rhs, \
								  south= south_rhs, \
								  center= center_rhs \
							   )
					print(expr)
	
					fout.write(expr+"\n")
	fout.close()


if __name__ == "__main__":
	gen_stencil2d_cse()


