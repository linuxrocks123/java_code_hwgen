#! /usr/bin/env python

#Java Homework Generator
#(c) 2015 Patrick Simmons
#You may redistribute this code under the General Public License version 3
#as published by the Free Software Foundation, or, at your option, any later
#version of that license.


import functools
import random
import sys

#Single argument determines all aspects of random code generation
if __name__=="__main__":
    flags = int(sys.argv[1])

class JT:
    BOOLEAN=-1
    BYTE=0
    CHAR=1
    SHORT=2
    INT=3
    LONG=4
    FLOAT=5
    DOUBLE=6
    STRING=-2
    UNKNOWN=-99

    TO_STR = { BOOLEAN : "boolean", BYTE : "byte", CHAR : "char",
               SHORT : "short", INT : "int", LONG : "long", FLOAT : "float",
               DOUBLE : "double", STRING : "String" }
    
    RANGES = { BYTE : (-128,127), SHORT : (-32768,32767),
               CHAR : (32,126), INT : (-2147483648,2147483647),
               LONG : (-9223372036854775808,9223372036854775807) }


class JE:
    def get_textual_representation(self):
        code = self.pattern
        for i in range(len(self.subexprs)):
            code = code.replace("$"+repr(i+1),self.subexprs[i].get_textual_representation())
        return code

    def typecheck(self):
        if self.jtype==JT.CHAR:
            self.value%=256
        elif self.jtype==JT.BYTE:
            self.value%=256
            if self.value > 127:
                self.value-=256
        elif self.jtype==JT.SHORT:
            self.value%=65536
            if self.value > 32767:
                self.value-=65536

    #Precedences:
    # 0: literal
    # 1: unary -, casts
    # 2: *,/,%
    # 3: +, -
    # 5: <, <=, >=, >
    # 6: ==, !=
    # 7: &&
    # 8: ||
    def __init__(self,pattern,subexprs,value,jtype,precedence):
        self.pattern = pattern
        self.subexprs = subexprs
        self.value = value
        self.jtype = jtype
        self.precedence = precedence
        self.typecheck()


#Dictionary: (returns, param1, ...) : generator_func:
rdict = {}
NAMES = ("var","var2","x","y","z","pasta","pizza","banana","potato","bunny",
         "cecile", "steve","chong","van","aubrey", "candy","froyo","xkcd","gpf",
         "red","orange","yellow","green","blue","violet","black","white","gray",
         "tan","teal","cyan","magenta","yellow","dont","mess","with","texas",
         "georgia","louisiana","illinois")
PRECLEVEL = { '*' : 2, '/' : 2, '%' : 2, '+' : 3, '-' : 3 }    
B_PRECS = { "<" : 5, "<=" : 5, ">=" : 5, ">" : 5, "==" : 6, "!=" : 6 }
BLOG_PRECS = { "&&" : 7, "||" : 8 }

#Rules for numeric type promotion in Java
def binop_promotion(jtype1,jtype2):
    return jtype2 if jtype2 > jtype1 else jtype1

def do_cast(val,jfrom,jto):
    if jfrom >= 5 and jto < 5:
        val = int(val)
    elif jfrom < 5 and jto >= 5:
        val = float(val)
    return val

def prettyprint(subje2):
    if subje2.jtype==JT.STRING:
        subje2_value = subje2.value
    elif subje2.jtype==JT.CHAR:
        subje2_value = chr(subje2.value) if subje2.value < 256 else chr(subje2.value%256)
    elif subje2.jtype==JT.BOOLEAN:
        subje2_value = repr(subje2.value==True).lower()
    elif subje2.jtype >= 5:
        subje2_value = "{0:.2f}".format(subje2.value)
    else:
        subje2_value = repr(subje2.value)
    return subje2_value

#Random Expression Generator
class Rand_Exp:
    def add_to_rdict(typetuple,generator):
        if typetuple not in rdict:
            rdict[typetuple]=[]
        rdict[typetuple].append(generator)

    #Literals
    
    def gen_boolean_literal():
        x = random.randint(0,1)
        return JE("true" if x else "false",[],x,JT.BOOLEAN,0)
    add_to_rdict((0,JT.BOOLEAN),gen_boolean_literal)

    def gen_char_literal():
        x = random.randint(32,126)
        return JE("'"+chr(x)+"'",[],x,JT.CHAR,0)
    add_to_rdict((0,JT.CHAR),gen_char_literal)
    
    def gen_int_literal():
        x = random.randint(0,100)
        return JE(repr(x),[],x,JT.INT,0)
    add_to_rdict((0,JT.INT),gen_int_literal)

    def gen_float_literal():
        x = float(repr(random.randint(0,100))+"."+repr(random.randint(0,100)))
        return JE(repr(x)+"f",[],x,JT.FLOAT,0)
    add_to_rdict((0,JT.FLOAT),gen_float_literal)
    
    def gen_double_literal():
        x = float(repr(random.randint(0,100))+"."+repr(random.randint(0,100)))
        return JE(repr(x),[],x,JT.DOUBLE,0)
    add_to_rdict((0,JT.DOUBLE),gen_double_literal)

    def gen_str_literal():
        x = NAMES[random.randint(0,len(NAMES)-1)]
        return JE('"'+x+'"',[],x,JT.STRING,0)
    add_to_rdict((0,JT.STRING),gen_str_literal)

    #Operators
    
    @staticmethod
    def parentheses(subje):
        return JE("($1)",[subje],subje.value,subje.jtype,0)

    def unary_negation(subje):
        return JE("-$1",[subje],-subje.value,subje.jtype if subje.jtype!=JT.CHAR else JT.INT,1)
    for x in (JT.INT,JT.FLOAT,JT.DOUBLE):
        add_to_rdict((1,x,x),unary_negation)
    add_to_rdict((1,JT.INT,JT.CHAR),unary_negation)
    
    def bool_not(subje):
        return JE("!$1",[subje],not subje.value,JT.BOOLEAN,1)
    add_to_rdict((1,JT.BOOLEAN,JT.BOOLEAN),bool_not)

    def binary_arithmetic(op,subje1,subje2):
        return JE("$1"+op+"$2",[subje1,subje2],eval(repr(subje1.value)+op+repr(subje2.value)),binop_promotion(subje1.jtype,subje2.jtype),PRECLEVEL[op])
    for op in PRECLEVEL:
        for jtype1 in (JT.BYTE,JT.CHAR,JT.SHORT,JT.INT,JT.LONG,JT.FLOAT,JT.DOUBLE):
            for jtype2 in (JT.BYTE,JT.CHAR,JT.SHORT,JT.INT,JT.LONG,JT.FLOAT,JT.DOUBLE):
                add_to_rdict((PRECLEVEL[op],binop_promotion(jtype1,jtype2),jtype1,jtype2),functools.partial(binary_arithmetic,op))

    def boolean_comparison(op,subje1,subje2):
        return JE("$1"+op+"$2",[subje1,subje2],eval(repr(subje1.value)+op+repr(subje2.value)),JT.BOOLEAN,B_PRECS[op])
    for op in B_PRECS:
        for jtype1 in (JT.BYTE,JT.CHAR,JT.SHORT,JT.INT,JT.LONG,JT.FLOAT,JT.DOUBLE):
            for jtype2 in (JT.BYTE,JT.CHAR,JT.SHORT,JT.INT,JT.LONG,JT.FLOAT,JT.DOUBLE):
                add_to_rdict((B_PRECS[op],JT.BOOLEAN,jtype1,jtype2),functools.partial(boolean_comparison,op))

    def boolean_logic(op,subje1,subje2):
        return JE("$1 "+op+" $2",[subje1,subje2],eval(repr(subje1.value)+" "+op.replace("&&","and").replace("||","or")+" "+repr(subje2.value)),JT.BOOLEAN,BLOG_PRECS[op])
    for op in BLOG_PRECS:
        add_to_rdict((BLOG_PRECS[op],JT.BOOLEAN,JT.BOOLEAN,JT.BOOLEAN),functools.partial(boolean_logic,op))

    def string_concatenation(subje1,subje2):
        subje2_value = prettyprint(subje2)
        return JE("$1+$2",[subje1,subje2],subje1.value+subje2_value,JT.STRING,3)
    for i in range(-2,7):
        add_to_rdict((3,JT.STRING,JT.STRING,i),string_concatenation)
    
    def explicit_cast(jtype,subje):
        return JE("("+JT.TO_STR[jtype]+")$1",[subje],do_cast(subje.value,subje.jtype,jtype),jtype,1)
    for i in range(0,7):
        for j in range(0,7):
            add_to_rdict((1,i,j),functools.partial(explicit_cast,i))

    @staticmethod
    def get_expr_generator(return_type,*subtypes):
        subtuple = [return_type]
        subtuple.extend(subtypes)
        subtuple = tuple(subtuple)
        
        keys = rdict.keys()
        endpos = random.randint(1,len(keys)-1)
        current_pos = endpos + 1
        while current_pos!=endpos:
            if current_pos==len(keys):
                current_pos = 0
            if keys[current_pos][1:]==subtuple:
                optionlist = rdict[keys[current_pos]]
                chosen = optionlist[random.randint(0,len(optionlist)-1)]
                return (keys[current_pos][0],chosen)
            current_pos+=1
        return None


#Symbol table: { JT.INT : [("name",value),...]}
symtab = {}

#Get variable from symtab
def get_var_of_type(jtype):
    if jtype in symtab:
        possibilities = symtab[jtype]
        return possibilities[random.randint(0,len(possibilities)-1)][1]
    return None

def gen_complex_expr(level,jtype=-99):
    #Get random type if we don't have one.
    if jtype==-99:
        jtype = random.randint(-2,6)
        
    if level==0:
        if random.randint(0,1)==0:
            varexp = get_var_of_type(jtype)
            if varexp!=None:
                return varexp
        generator = Rand_Exp.get_expr_generator(jtype)
        if generator!=None:
            return generator[1]()
        else:
            jtype+=1
            if jtype==7:
                jtype=-2
            return gen_complex_expr(0,jtype)


    #Handle parentheses.
    subexprs = []
    def gen_parentheses(precedence,generator):
        #Handle precedence
        if precedence < subexprs[0].precedence:
            subexprs[0] = Rand_Exp.parentheses(subexprs[0])

        #Most of the time, equal-precedence operations need no parentheses.
        #However, the associativity of precedence 2 operators (*,/,%) matters.
        #Therefore, if we are of precedence 2, we must check if our right
        #subexpression is also of precedence 2.  If so, we must parenthesize it.
        if len(subexprs)==2 and precedence < subexprs[1].precedence or precedence==2 and subexprs[1].precedence==2:
            subexprs[1] = Rand_Exp.parentheses(subexprs[1])
        elif len(subexprs)==1 and precedence==subexprs[0].precedence:
            subexprs[0] = Rand_Exp.parentheses(subexprs[0])
        elif len(subexprs)==2 and subexprs[1].precedence==1 and subexprs[1].jtype!=JT.BOOLEAN and type(generator)==functools.partial and generator.args[0]=='-':
            subexprs[1] = Rand_Exp.parentheses(subexprs[1])
        elif len(subexprs)==2 and precedence==3 and subexprs[1].precedence==3 and subexprs[0].jtype==JT.STRING and subexprs[1].jtype!=JT.STRING:
            subexprs[1] = Rand_Exp.parentheses(subexprs[1])
        
        #We also must check if our right subexpression is equal to 0 for / & %.
        if len(subexprs)==2 and type(generator)==functools.partial and generator.args[0] in ('/','%') and subexprs[1].value==0:
            generator = functools.partial(Rand_Exp.binary_arithmetic.__func__,'*')
        return (precedence,generator)

    #We are not the base case: generate one or two subexpressions
    subexprs.append(gen_complex_expr(level-1))
    if random.randint(1,5)!=5: #generate two subexpressions
        subexprs.append(gen_complex_expr(level-1))

    #Helper to get type list from subexprs
    def get_subtypes():
        to_return = []
        for x in subexprs:
            to_return.append(x.jtype)
        return to_return

    #jtype iteration
    def inc_jtype(jtype):
        jtype+=1
        if jtype==7:
            jtype=-2
        return jtype

    #Try various configurations to get a valid generator
    generator = None
    orig_jtype = jtype

    while True:
        generator = Rand_Exp.get_expr_generator(jtype,*get_subtypes())
        jtype = inc_jtype(jtype)
        if generator!=None or jtype==orig_jtype:
            break
    
    while generator==None:
        generator = Rand_Exp.get_expr_generator(jtype,*get_subtypes())
        if generator==None:
            if len(subexprs)==1:
                subexprs.append(gen_complex_expr(level-1))
                continue
            subexprs.reverse()
            generator = Rand_Exp.get_expr_generator(jtype,*get_subtypes())
        if generator==None:
            subexprs.reverse()
            backup = subexprs
            subexprs = [subexprs[0]]
            generator = Rand_Exp.get_expr_generator(jtype,*get_subtypes())
        if generator==None and len(backup)==2:
            subexprs = [backup[1]]
            generator = Rand_Exp.get_expr_generator(jtype,*get_subtypes())
        if generator==None:
            subexprs = backup
            jtype = inc_jtype(jtype)

    #Okay, we have a valid generator.  Parenthesize, if needed.
    generator = gen_parentheses(*generator)

    return generator[1](*subexprs)

#Get new varname
def get_new_varname():
    no_good_name = True
    while no_good_name:
        no_good_name = False
        proposed_name = NAMES[random.randint(0,len(NAMES)-1)]
        for jtype in symtab:
            for var in symtab[jtype]:
                if var[0]==proposed_name:
                    no_good_name = True
                    break
            if no_good_name:
                break
        if not no_good_name:
            return proposed_name

#Insert new variable into symbol table
def create_new_var(varname,init_expr):
    if init_expr.jtype not in symtab:
        symtab[init_expr.jtype]=[]
    to_append = symtab[init_expr.jtype]
    to_append.append((varname,JE(varname,[],init_expr.value,init_expr.jtype,0)))

#Reassign value of variable in symbol table
def assign_var(varname,expr):
    for jtype in symtab:
        for var in symtab[jtype]:
            if var[0]==varname:
                if expr.jtype==jtype:
                    var[1].value = expr.value
                elif expr.jtype>=0 and expr.jtype<=6 and expr.jtype < jtype:
                    var[1].value = do_cast(expr.value,expr.jtype,jtype)
                else:
                    return None

question = open("question.txt","w")
answer = open("answer.txt","w")

if flags==1:
    for i in range(1,11):
        q = gen_complex_expr(3)
        question.write(repr(i)+".\n"+q.get_textual_representation()+"\n\n")
        answer.write(JT.TO_STR[q.jtype]+" / "+prettyprint(q)+"\n")
elif flags==2:
    for _ in range(random.randint(1,15)):
        q = gen_complex_expr(3)
        if q.jtype >= JT.BYTE and q.jtype < JT.DOUBLE:
            jtype = random.randint(q.jtype,JT.DOUBLE)
        else:
            jtype = q.jtype
        if jtype not in symtab or not random.randint(0,3):
            question.write(JT.TO_STR[jtype]+" ")
            varname = get_new_varname()
            create_new_var(varname,q)
        else:
            varname = symtab[jtype][random.randint(0,len(symtab[jtype])-1)][0]
            assign_var(varname,q)
        question.write(varname+"="+q.get_textual_representation()+";\n")
    varsyms = []
    for jtype in symtab:
        for var in symtab[jtype]:
            varsyms.append(var)
    varsyms.sort()
    for var in varsyms:
        answer.write(var[0]+": "+prettyprint(var[1])+"\n")
