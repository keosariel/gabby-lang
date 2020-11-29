def data(Type,value):
    '''
    Type (NAME | FLOAT | NUMBER | STRING)
    '''
    return(Type,{'value':value})

def expression(op,lhs,rhs):
    '''
    lhs (left-hand-side)
    rhs (right-hand-side)
    op (operator)
    '''

    return ('Expression',{'op':op,'lhs':lhs,'rhs':rhs})

def var_assign(name,value):
    '''
    var name = value
    '''
    return('VarAssign',{'value':value,'name':name})

def if_stmt(body,orelse,test):

    return ('If',{'body':body,'test':test,'orelse':orelse})

def while_block(body,test):

    return ('While',{'test':test,'body':body})

def until_block(body,test):

    return ('Until',{'test':test,'body':body})

def func_call(name,params):
    '''
    name (params*)
    '''
    return ('FuncCall',{'params':params,'name':name})

def function(name,def_params,ret,body):
    '''
    def name (def_params*) : return_type
    '''
    
    return ('Def',{'name':name,'return':ret,'body':body, 'def_params':def_params if def_params else []})
