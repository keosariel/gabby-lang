from src.pparser.Lexer import PLexer
from src.pparser.Parser import PParser

from llvmlite import ir
import pprint

class Compiler:
    
    def __init__(self):
        self.type_map = {
            'bool':ir.IntType(1),
            'int':ir.IntType(32),
            'float':ir.FloatType(),
            'double':ir.DoubleType(),
            'void':ir.VoidType(),
            'str':ir.ArrayType(ir.IntType(8),1), # Note i8 in most languages are characters
        }

        self.module = ir.Module('main')
        
        # Defining builtin function (printf)
        fnty = ir.FunctionType(self.type_map['int'], [ir.IntType(8).as_pointer()], var_arg=True)
        func = ir.Function(self.module, fnty, 'printf')

        # This helps to keep track of Defined Variabled
        self.variables = {'printf':(func,ir.IntType(32))}
        
        # Current Builder
        self.builder = None
        
        self.i = 0
        
    def inc(self):
        self.i += 1
        return 1

    def compile(self,ast):
        for branch in ast:
            # branch[0] holds the branch type (from the ast)
            if branch[0] == 'VarAssign':
                self.visit_assign(branch)
            elif branch[0] == 'Def':
                self.visit_def(branch)
            elif branch[0] == 'Return':
                self.visit_return(branch)
            elif branch[0] == 'If':
                self.visit_if(branch)
            elif branch[0] == 'While':
                self.visit_while(branch)
            elif branch[0] == 'Until':
                self.visit_until(branch)
            elif branch[0] == 'FuncCall':
                self.visit_funccall(branch)
                
    def visit_def(self,branch):
        name = branch[1]['name']
        body = branch[1]['body']
        params = branch[1]['def_params']
        params = params if params[0] else []

        # Keep track of the name of each parameter
        params_name = [x['name'] for x in params]
        
        # Keep track of the types of each parameter
        params_type = [self.type_map[x['type']] for x in params]

        # Functions return type
        return_type = self.type_map[branch[1]['return']]

        # Defining a funtions (return type,  parameters)
        fnty = ir.FunctionType(return_type,params_type)
        func = ir.Function(self.module,fnty,name=name)

        # Defining function's block
        block = func.append_basic_block(f'{name}_entry')

        previous_builder = self.builder

        # Current builder
        self.builder = ir.IRBuilder(block)

        params_ptr = []
        
        # Storing the pointers of each parameter
        for i,typ in enumerate(params_type):
            ptr = self.builder.alloca(typ)
            self.builder.store(func.args[i],ptr)
            params_ptr.append(ptr)

        previous_variables = self.variables.copy()
        for i,x in enumerate(zip(params_type,params_name)):
            typ = params_type[i]
            ptr = params_ptr[i]
            
            # Add function's parameter to stored variables
            self.variables[x[1]] = ptr,typ

        # Adding function to variables
        self.variables[name] = func,return_type

        # Compile the body of the function 
        self.compile(body)

        # Removing the function's variables so it cannot be accessed by other functions
        self.variables = previous_variables
        self.variables[name] = func,return_type

        # Done with the function's builder
        # Return to the previous builder
        self.builder = previous_builder
        
    def visit_if(self,branch):
        orelse = branch[1]['orelse']
        body = branch[1]['body']
        test,Type = self.visit_value(branch[1]['test'])
        
        # If there is no else block
        if orelse == []:
          with self.builder.if_then(test):
              # Runs this if true
              self.compile(body)
        else:
            with self.builder.if_else(test) as (true,otherwise):
                # Creating a condition branch
                #      condition
                #        / \
                #     true  false
                #       /   \
                #      /     \
                # if block  else block
              with true:
                  # Runs this if true
                  self.compile(body)

              with otherwise:
                  # Runs this if false
                  self.compile(orelse)
                  
    def visit_value(self,branch):
        if branch[0] == 'Number':
            value,Type = branch[1]['value'],self.type_map['int']
            return ir.Constant(Type,value),Type
        
        elif branch[0] == 'Float':
            value,Type = branch[1]['value'],self.type_map['float']
            return ir.Constant(Type,value),Type
        
        elif branch[0] == 'Name':
            ptr,Type = self.variables[branch[1]['value']]  
            return self.builder.load(ptr),Type
        
        elif branch[0] == 'Expression':
            return self.visit_expression(branch)
        
        elif branch[0] == 'FuncCall':
                return self.visit_funccall(branch)
            
        elif branch[0] == 'String':
            value = branch[1]['value']
            string,Type = self.strings(value)
            return string, Type
        
    def visit_assign(self,branch):
        name = branch[1]['name']
        value = branch[1]['value']

        # Getting the value and it's type
        value,Type = self.visit_value(value)

        if not self.variables.__contains__(name):
            # Creating a pointer for the type 'Type' : ir.Type
            ptr = self.builder.alloca(Type)

            # Storing the value to the pointer
            self.builder.store(value,ptr)

            # Adding the name and it's pointer to
            # Variable map for easy retrieval
            self.variables[name] = ptr,Type
        else:
            ptr,_ = self.variables[name]
            self.builder.store(value,ptr)
        
    def strings(self,string):
        """Strings are converted to an array of characters"""
        
        string = string[1:-1]
        string = string.replace('\\n','\n\0')
        n = len(string)+1
        buf = bytearray((' ' * n).encode('ascii'))
        buf[-1] = 0
        buf[:-1] = string.encode('utf8')
        return ir.Constant(ir.ArrayType(ir.IntType(8), n), buf),ir.ArrayType(ir.IntType(8), n)
    
    def printf(self,params,Type):
        """C builtin Printf function"""
        
        format = params[0]
        params = params[1:]
        zero = ir.Constant(ir.IntType(32),0)
        ptr = self.builder.alloca(Type)
        self.builder.store(format,ptr)
        format = ptr
        format = self.builder.gep(format, [zero, zero])
        format = self.builder.bitcast(format, ir.IntType(8).as_pointer())
        func,_ = self.variables['printf']
        return self.builder.call(func,[format,*params])
    
    def visit_funccall(self,branch):
        name = branch[1]['name']
        params = branch[1]['params']

        args = []
        types = []
        if params[0]:
            for x in params:
                val,_ = self.visit_value(x)
                args.append(val)
                types.append(_)

        if name == 'printf':
            ret = self.printf(args,types[0])
            ret_type = self.type_map['int']
        else:
            func,ret_type = self.variables[name]
            ret = self.builder.call(func,args)

        return ret, ret_type
    
    def visit_while(self,branch):
        Test = branch[1]['test']
        body = branch[1]['body']
        test,_ = self.visit_value(Test)

        # Entry (block where that runs if the condition is true)
        while_loop_entry = self.builder.append_basic_block("while_loop_entry"+str(self.inc()))

        # If the condition is not true it runs from here
        while_loop_otherwise = self.builder.append_basic_block("while_loop_otherwise"+str(self.i))

        # Creating a condition branch
        #     condition
        #        / \
        # if true   if false
        #       /   \
        #      /     \
        # true block  false block
        self.builder.cbranch(test, while_loop_entry, while_loop_otherwise)

        # Setting the builder position-at-start
        self.builder.position_at_start(while_loop_entry)
        self.compile(body)
        test,_ = self.visit_value(Test)
        self.builder.cbranch(test, while_loop_entry, while_loop_otherwise)
        self.builder.position_at_start(while_loop_otherwise)
    
    def visit_until(self,branch):
        Test = branch[1]['test']
        body = branch[1]['body']
        test,_ = self.visit_value(Test)
        test = self.builder.not_(test)

        # Entry (block where that runs if the condition is not true)
        until_loop_entry = self.builder.append_basic_block("until_loop_entry"+str(self.inc()))

        # If the condition is true it runs from here
        until_loop_otherwise = self.builder.append_basic_block("until_loop_otherwise"+str(self.i))

        # Creating a condition branch
        #     condition
        #        / \
        # if false  if true
        #       /   \
        #      /     \
        # true block  false block
        self.builder.cbranch(test, until_loop_entry, until_loop_otherwise)

        # Setting the builder position-at-start
        self.builder.position_at_start(until_loop_entry)
        self.compile(body)
        test,_ = self.visit_value(Test)
        test = self.builder.not_(test)
        self.builder.cbranch(test, until_loop_entry, until_loop_otherwise)
        self.builder.position_at_start(until_loop_otherwise)
    

    def visit_return(self,branch):
        value = branch[1]['value']
        value,Type = self.visit_value(value)
        self.builder.ret(value)

    def visit_expression(self,branch):
        op = branch[1]['op']
        lhs, lhs_type = self.visit_value(branch[1]['lhs'])
        rhs, rhs_type = self.visit_value(branch[1]['rhs'])

        if isinstance(rhs_type,ir.FloatType) and isinstance(lhs_type,ir.FloatType):
            Type = ir.FloatType()
            if op == '+':
                value = self.builder.fadd(lhs,rhs)
            elif op == '*':
                value = self.builder.fmul(lhs,rhs)
            elif op == '/':
                 value = self.builder.fdiv(lhs,rhs)
            elif op == '%':
                 value = self.builder.frem(lhs,rhs)
            elif op == '-':
                 value = self.builder.fsub(lhs,rhs)
            elif op == '<':
                value = self.builder.fcmp_ordered('<',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '<=':
                value = self.builder.fcmp_ordered('<=',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '>':
                value = self.builder.fcmp_ordered('>',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '>=':
                value = self.builder.fcmp_ordered('>=',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '!=':
                value = self.builder.fcmp_ordered('!=',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '==':
                value = self.builder.fcmp_ordered('==',lhs,rhs)
                Type = ir.IntType(1)
        
        elif isinstance(rhs_type,ir.IntType) and isinstance(lhs_type,ir.IntType):
            Type = ir.IntType(32)
            if op == '+':
                value = self.builder.add(lhs,rhs)
            elif op == '*':
                value = self.builder.mul(lhs,rhs)
            elif op == '/':
                value = self.builder.sdiv(lhs,rhs)
            elif op == '%':
                value = self.builder.srem(lhs,rhs)
            elif op == '-':
                value = self.builder.sub(lhs,rhs)
            elif op == '<':
                value = self.builder.icmp_signed('<',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '<=':
                value = self.builder.icmp_signed('<=',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '>':
                value = self.builder.icmp_signed('>',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '>=':
                value = self.builder.icmp_signed('>=',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '!=':
                value = self.builder.icmp_signed('!=',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '==':
                value = self.builder.icmp_signed('==',lhs,rhs)
                Type = ir.IntType(1)
            elif op == '&':
                value = self.builder.and_(lhs,rhs)
                Type = ir.IntType(1)
            elif op == '|':
                value = self.builder.or_(lhs,rhs)
                Type = ir.IntType(1)
            elif op == '^':
                value = self.builder.xor(lhs,rhs)
                Type = ir.IntType(1)
            elif op == '>>':
                value = self.builder.ashr(lhs,rhs)
                Type = ir.IntType(1)
            elif op == '<<':
                value = self.builder.shl(lhs,rhs)
                Type = ir.IntType(1)
            
                
        return value,Type